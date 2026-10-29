import imaplib
import email
from email.header import decode_header
import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from app.config import settings

def decode_mime_words(raw_header: Optional[str]) -> str:
    """Safely decode MIME encoded email headers (e.g. =?UTF-8?B?...?=)."""
    if not raw_header:
        return ""
    decoded_fragments = []
    try:
        parts = decode_header(raw_header)
        for fragment, encoding in parts:
            if isinstance(fragment, bytes):
                enc = encoding or "utf-8"
                try:
                    decoded_fragments.append(fragment.decode(enc, errors="replace"))
                except LookupError:
                    decoded_fragments.append(fragment.decode("utf-8", errors="replace"))
            else:
                decoded_fragments.append(str(fragment))
        return "".join(decoded_fragments)
    except Exception:
        return str(raw_header)

def format_imap_error(err: Any) -> str:
    err_str = str(err)
    if "AUTHENTICATIONFAILED" in err_str or "Invalid credentials" in err_str:
        return "Yahoo authentication failed: Invalid email address or App Password. Please ensure you generated a 16-character App Password from Yahoo Account Security settings."
    if "timed out" in err_str.lower():
        return "Connection timed out while reaching imap.mail.yahoo.com:993. Please verify network access."
    return err_str.replace("b'", "").replace("'", "")

class YahooIMAPClient:
    def __init__(
        self,
        email_address: str,
        secret: str,
        auth_type: str = "app_password",
        server: str = "imap.mail.yahoo.com",
        port: int = 993,
        timeout: int = 20
    ):
        self.email_address = email_address.strip()
        self.secret = secret.strip()
        self.auth_type = auth_type
        self.server = server.strip()
        self.port = port
        self.timeout = timeout
        self.connection: Optional[imaplib.IMAP4_SSL] = None

    def connect(self) -> Tuple[bool, str]:
        """Establish secure SSL connection to Yahoo IMAP server and authenticate."""
        try:
            self.connection = imaplib.IMAP4_SSL(self.server, self.port, timeout=self.timeout)
            if self.auth_type == "oauth2":
                # Yahoo XOAUTH2 format: user={email}\x01auth=Bearer {token}\x01\x01
                auth_string = f"user={self.email_address}\x01auth=Bearer {self.secret}\x01\x01"
                self.connection.authenticate('XOAUTH2', lambda x: auth_string)
            else:
                # Yahoo App Password (strip any whitespace)
                clean_pass = self.secret.replace(" ", "")
                self.connection.login(self.email_address, clean_pass)
            return True, "Successfully connected to Yahoo Mail"
        except imaplib.IMAP4.error as e:
            return False, format_imap_error(e)
        except Exception as e:
            return False, format_imap_error(e)

    def disconnect(self):
        """Safely close and logout from IMAP connection."""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            try:
                self.connection.logout()
            except Exception:
                pass
            self.connection = None

    def fetch_new_emails(
        self,
        folder: str = "INBOX",
        last_uid: int = 0,
        max_results: int = 50,
        save_attachments_dir: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """
        Incrementally fetch emails with UID > last_uid.
        Returns list of parsed email dictionaries.
        """
        if not self.connection:
            raise RuntimeError("IMAP client is not connected")

        # Select folder (read-only=False to allow marking or read-only=True to prevent accidental modifications)
        status, _ = self.connection.select(f'"{folder}"', readonly=True)
        if status != "OK":
            raise RuntimeError(f"Unable to select mailbox folder: {folder}")

        # Search for messages incrementally
        if last_uid > 0:
            search_query = f"UID {last_uid + 1}:*"
        else:
            search_query = "ALL"

        status, data = self.connection.uid("SEARCH", None, search_query)
        if status != "OK" or not data or not data[0]:
            return []

        uid_list = [int(u) for u in data[0].split() if u.isdigit()]
        # Filter out uids <= last_uid if server returns current uid
        uid_list = [u for u in uid_list if u > last_uid]
        uid_list.sort()

        if max_results and len(uid_list) > max_results:
            # Take the newest batch
            uid_list = uid_list[-max_results:]

        results = []
        for uid in uid_list:
            try:
                msg_dict = self._fetch_single_email(uid, save_attachments_dir)
                if msg_dict:
                    results.append(msg_dict)
            except Exception as e:
                print(f"Error fetching email UID {uid}: {e}")

        return results

    def _fetch_single_email(self, uid: int, save_attachments_dir: Optional[Path]) -> Optional[Dict[str, Any]]:
        status, data = self.connection.uid("FETCH", str(uid), "(RFC822)")
        if status != "OK" or not data:
            return None

        raw_email_bytes = None
        for response_part in data:
            if isinstance(response_part, tuple) and len(response_part) > 1:
                raw_email_bytes = response_part[1]
                break

        if not raw_email_bytes:
            return None

        msg = email.message_from_bytes(raw_email_bytes)

        message_id = msg.get("Message-ID", f"synthetic-{uuid.uuid4()}")
        subject = decode_mime_words(msg.get("Subject", ""))
        sender = decode_mime_words(msg.get("From", ""))
        recipient = decode_mime_words(msg.get("To", ""))
        date_str = msg.get("Date", "")

        body_plain = ""
        body_html = ""
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition.lower() or part.get_filename():
                    # Handle Attachment
                    filename = decode_mime_words(part.get_filename() or f"attachment_{uuid.uuid4().hex[:8]}")
                    payload = part.get_payload(decode=True)
                    if payload and save_attachments_dir:
                        file_ext = Path(filename).suffix.lower()
                        safe_name = f"{uuid.uuid4().hex[:10]}_{re_sanitize_filename(filename)}"
                        file_path = save_attachments_dir / safe_name
                        with open(file_path, "wb") as f:
                            f.write(payload)

                        attachments.append({
                            "file_name": filename,
                            "file_path": str(file_path),
                            "file_type": file_ext.replace(".", ""),
                            "file_size": len(payload)
                        })
                else:
                    # Body text
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        try:
                            decoded_text = payload.decode(charset, errors="replace")
                        except Exception:
                            decoded_text = payload.decode("utf-8", errors="replace")

                        if content_type == "text/plain":
                            body_plain += decoded_text + "\n"
                        elif content_type == "text/html":
                            body_html += decoded_text + "\n"
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                try:
                    decoded_text = payload.decode(charset, errors="replace")
                except Exception:
                    decoded_text = payload.decode("utf-8", errors="replace")

                if msg.get_content_type() == "text/html":
                    body_html = decoded_text
                else:
                    body_plain = decoded_text

        return {
            "uid": uid,
            "message_id": message_id,
            "subject": subject,
            "sender": sender,
            "recipient": recipient,
            "date_str": date_str,
            "body_plain": body_plain.strip(),
            "body_html": body_html.strip(),
            "attachments": attachments
        }

def re_sanitize_filename(filename: str) -> str:
    import re
    return re.sub(r'[^A-Za-z0-9_.-]', '_', filename)

def test_yahoo_connection(
    email_address: str,
    secret: str,
    auth_type: str = "app_password",
    server: str = "imap.mail.yahoo.com",
    port: int = 993
) -> Dict[str, Any]:
    """Test connection to Yahoo IMAP server and report mailbox stats."""
    client = YahooIMAPClient(email_address, secret, auth_type, server, port)
    ok, message = client.connect()
    if not ok:
        return {"success": False, "message": message, "unread_count": 0}

    try:
        # Check INBOX status
        status, data = client.connection.status("INBOX", "(MESSAGES UNSEEN)")
        messages_count = 0
        unseen_count = 0
        if status == "OK" and data:
            resp_str = data[0].decode("utf-8", errors="ignore")
            # Parse MESSAGES n UNSEEN m
            import re
            m = re.search(r'MESSAGES\s+(\d+)', resp_str)
            u = re.search(r'UNSEEN\s+(\d+)', resp_str)
            if m: messages_count = int(m.group(1))
            if u: unseen_count = int(u.group(1))

        client.disconnect()
        return {
            "success": True,
            "message": f"Successfully connected to Yahoo Mail. Total Messages: {messages_count}, Unseen: {unseen_count}",
            "messages_count": messages_count,
            "unseen_count": unseen_count
        }
    except Exception as e:
        client.disconnect()
        return {"success": False, "message": f"Connected, but mailbox query failed: {str(e)}", "unread_count": 0}
