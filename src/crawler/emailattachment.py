import imaplib
import email.utils
from email.header import decode_header
import datetime
import zipfile
import os
import re
from . import Crawler

EMAIL_SERVER = os.getenv("EMAIL_SERVER")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

class EmailCrawler(Crawler):
    """
    Fetch attachment from email using IMAP
    """
    def crawl_info(self, from_addr="service@mail.alipay.com", attachment_fn_pattern=".*pdf"):
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
                on {today} or {today - 1 day}
                """
                status, msg_data = mail.fetch(mail_id, "(RFC822)")
                if status != "OK":
                    continue
                msg = email.message_from_bytes(msg_data[0][1])
                msg_from_addr = email.utils.parseaddr(msg["From"])[1]
                if msg_from_addr != from_addr:
                    continue
                date = email.utils.parsedate_to_datetime(msg["Date"])
                if date.date() < datetime.date.today() - datetime.timedelta(days=1):
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
                    if re.search(attachment_fn_pattern, filename):
                        print(f"Found matching attachment: {filename}")
                        attachment_format = filename.split(".")[-1]
                        # save attachment
                        with open(self.save_fp, "wb") as f:
                            f.write(part.get_payload(decode=True))
                            print(f"Attachment saved to {self.save_fp}")
                    
                        # postprocess
                        ## extract zip attachment file
                        if attachment_format == "zip":
                            print(f"Extracting zip attachment: {self.save_fp}")
                            print("请输入提取密码:")
                            password = input()
                            try:
                                password = password.encode() if password else None
                                with zipfile.ZipFile(self.save_fp, "r") as zip_ref:
                                    zip_ref.extractall(os.path.dirname(self.save_fp), pwd=password) 
                                    ## rename extracted file
                                    orig_filename = zip_ref.namelist()[0]
                                    os.rename(os.path.join(os.path.dirname(self.save_fp), orig_filename), self.save_fp.replace(".zip", ".xlsx"))
                            except zipfile.BadZipFile:
                                print("密码错误，跳过提取")
                                continue
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
    # email_crawler = EmailCrawler(update_time="01:00", update_interval=86400, save_fp="datatables/eaccount_account.zip")
    # email_crawler = EmailCrawler(update_time="01:00", update_interval=86400, save_fp="datatables/yulibao_account.xlsx")
    # email_crawler.schedule_crawling()
    email_crawler.crawl_info()
    # email_crawler.crawl_info(from_addr="efund@chinaclear.com.cn", attachment_fn_pattern=".*zip")
    # email_crawler.crawl_info(from_addr="service@mail.mybank.cn", attachment_fn_pattern=".*xlsx")
