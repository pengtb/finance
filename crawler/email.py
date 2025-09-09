import imaplib
import email.utils
from email.header import decode_header
import datetime
from . import Crawler

EMAIL_SERVER = "imap.konojojo.icu"
EMAIL_PORT = 993
EMAIL_USER = "ptbian@konojojo.icu"
EMAIL_PASSWORD = "TD-LTEMCE16ptb"

class EmailCrawler(Crawler):
    """
    Fetch attachment from email using IMAP
    """
    def crawl_info(self, save=True):
        """
        Crawl email attachment
        """
        try:
            # login to email server
            mail = imaplib.IMAP4_SSL(EMAIL_SERVER, EMAIL_PORT)
            response, data = mail.login(EMAIL_USER, EMAIL_PASSWORD)
            if response != "OK":
                raise Exception("Error logging in to email server")
            response, data = mail.select("INBOX")
            if response != "OK":
                raise Exception("Error selecting INBOX")
            
            # fetch emails
            today = datetime.date.today().strftime("%d-%b-%Y")
            status, messages = mail.search(None, "ALL")
            if status != "OK":
                raise Exception("Error searching for emails")
            mail_ids = messages[0].split()
            if len(mail_ids) == 0:
                raise Exception("No emails found")
            
            # process emails: only the latest one
            for mail_id in reversed(mail_ids):
                ## filter emails
                """
                from service@mail.alipay.com
                on {today}
                """
                status, msg_data = mail.fetch(mail_id, "(RFC822)")
                if status != "OK":
                    continue
                msg = email.message_from_bytes(msg_data[0][1])
                from_addr = email.utils.parseaddr(msg["From"])[1]
                if from_addr != "service@mail.alipay.com":
                    continue
                date = email.utils.parsedate_to_datetime(msg["Date"])
                if date.date() != datetime.date.today():
                    continue
                
                ## fetch pdf attachment
                for part in msg.walk():
                    if part.get_content_maintype() == "multipart":
                        continue
                    if part.get("Content-Disposition") is None:
                        continue
                    filename = part.get_filename()
                    if filename is None:
                        continue
                    decoded_parts = decode_header(filename)
                    filename = ''.join([str(part[0], part[1] or 'utf-8') for part in decoded_parts])
                    print(filename)
                    if filename.lower().endswith(".pdf"):
                        print(f"Found pdf attachment: {filename}")
                        # save attachment
                        if save:
                            with open(self.save_fp, "wb") as f:
                                f.write(part.get_payload(decode=True))
                                print(f"Attachment saved to {self.save_fp}")
                        break
                            
            # logout
            mail.close()
            mail.logout()
        except Exception as e:
            try:
                mail.close()
                mail.logout()
            except:
                pass
            print(f"Error: {e}")
            raise e
        
if __name__ == "__main__":
    email_crawler = EmailCrawler(update_time="01:00", update_interval=86400, save_fp="datatables/alipay_account.pdf")
    # email_crawler.schedule_crawling()
    email_crawler.crawl_info()