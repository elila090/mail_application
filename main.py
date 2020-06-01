import requests
from bs4 import BeautifulSoup
import redis

from secrets import from_email, password, to_email, KEYWORDS, urls


def email():
    r = redis.Redis(host='localhost', port=6379, db=0)
    links = [r.get(k) for k in r.keys()]

    # email
    import smtplib

    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    sender = from_email
    receiver = to_email

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Link"
    msg['From'] = sender
    msg['To'] = receiver

    html = """
            <h3 style="color: #2e6c80;">Hej på dig!</h3>
                <p><span style="color: #333333;">Här kommer %s länkar som kan vara intressanta för dig baserade på dina keywords:</span></p>
                    <ul>
                        %s
                    </ul>
                <p><span style="color: #333333;"><em>Dina keywords sedan tidigare är: %s</em></span></p>
                <p>&nbsp;</p>
            """ % (len(links), "".join(['<li style="clear: both;"><span style="color: #333333;">{0}</span></li>'.format(link)
                                        for link in links]), ", ".join(KEYWORDS))

    # Record the MIME type text/html.
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part2)

    try:
        # Send the message via local SMTP server.
        mail = smtplib.SMTP('smtp.gmail.com', 587)
        mail.ehlo()
        mail.starttls()

        mail.login(sender, password)
        mail.sendmail(sender, receiver, msg.as_string())
        mail.quit()
    except Exception as e:
        print("Error ", e, " occurred.")

    # empty db
    r.flushdb()
    print("Email sent and db is flushed.")


class Scraper:
    def __init__(self, keywords):
        #self.markup = requests.get(url=urls[0]).text     # test with only one url
        self.keywords = keywords

    def parse(self):
        links = []
        for url in urls:
            markup = requests.get(url=url).text
            soup = BeautifulSoup(markup, 'html.parser')

            links += soup.findAll("a", {"class": "storylink"})       # specific to "Hacker News" site.
            links += soup.findAll("h3", {"class": "post-item_title"})
            links += soup.findAll("a", {"class": "blog_post_card__title-link"})
            #links = soup.findAll("h3", {"class": "t-entry-title h3"})

        self.saved_links = []
        for link in links:
            for keyword in self.keywords:
                if keyword in link.text:
                    self.saved_links.append(link)

    def store(self):
        r = redis.Redis(host='localhost', port=6379, db=0)
        for link in self.saved_links:
            r.set(link.text, str(link))


s = Scraper(KEYWORDS)
s.parse()
s.store()
email()
