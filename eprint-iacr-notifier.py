#!/usr/bin/env python2.7

from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import urllib2
import sys
import smtplib

# please set to true when you are debugging and you don't want to send emails
simulate_email=False
#simulate_email=True
# please set to true when you are debugging and you don't want to update the conf file with the latest paper ID
simulate_conf_update=False
#simulate_conf_update=True

def get_url(url):
    print "Downloading page at", url, "...",
    response = urllib2.urlopen(url)
    html = response.read()
    print " Done."
    return html

def dedup_spaces(string):
    return " ".join(string.split())

def process_paper(base_url, paper_id, parser):
    url = base_url + str(paper_id)
    paper_html = get_url(url)

    soup = BeautifulSoup(paper_html, parser)

    bs = soup.find_all('b')
    title = bs[0].text
    authors = soup.find('i')
    
    title = dedup_spaces(title)
    authors = dedup_spaces(authors.text)
    # TODO: for some papers, after <b>Abstract:</b> there could be tags like <p /> in the abstract itself (see https://eprint.iacr.org/2019/868 for example) which means bs[1].next_sibling won't get the full abstract
    #print "bs[1]:", bs[1]
    #print "bs[1].next_sibling:", bs[1].next_sibling
    #print "bs[1].next_sibling.next_sibling:", bs[1].next_sibling.next_sibling
    #print "bs[1].next_sibling.next_sibling.next_sibling:", bs[1].next_sibling.next_sibling.next_sibling
    #print "bs[1].next_sibling.next_sibling.next_sibling.next_sibling:", bs[1].next_sibling.next_sibling.next_sibling.next_sibling
    abstract = dedup_spaces(bs[1].next_sibling)
    pdflink = url + ".pdf"
    
    #print " * Title:", title
    #print " * Authors:", authors
    #print " * Abstract:", abstract
    #print " * PDF: ", pdflink
    #print

    return title, authors, abstract, pdflink
    
def test_gmail(username, passwd):
    print "Testing " + username + "@gmail.com with password '" + passwd + "'"
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(username, passwd);
    server.quit()

if len(sys.argv) < 5:
    print "Usage:", sys.argv[0], "<notified-email-address> <sender-Gmail-address> <sender-Gmail-password> <conf-file>"
    sys.exit(1)

notified_email = sys.argv[1]
sender_gmail_addr = sys.argv[2]
sender_gmail_username = sender_gmail_addr.split("@")[0]
sender_gmail_passw = sys.argv[3]
conf_file = sys.argv[4]

test_gmail(sender_gmail_username, sender_gmail_passw)

parser = "lxml"

# open file for both reading and writing
f = open(conf_file, "rw+")
# read year from file
year = int(f.readline())
# read last paper's ID from file
last_paper_id = f.readline()
url = "http://eprint.iacr.org/" + str(year) + "/"

if last_paper_id == '':
    print "ERROR: '" +  conf_file + "' file is empty. Please type the paper ID that you want to start from."
    sys.exit(1)

last_paper_id = int(last_paper_id)
print "Last paper ID:", last_paper_id

# download eprint index
index_html = get_url(url)

soup = BeautifulSoup(index_html, parser)

# parse papers
#print "New paper IDs:"
skipped = []    # keep track of skipped links, for debugging purposes
new_last_paper_id = last_paper_id
email_html="New papers have been published on the Cryptology ePrint Archive!<br /><br />\n"
email_text="New papers have been published on the Cryptology ePrint Archive!\n\n"
for link in soup.find_all('a'):
    link = link.get('href')
    # links will be of the form /<year>/<paper-id> and /<year>/<paper-id>.pdf
    split = link.split(".")

    # if it's a PDF link, skip
    if len(split) == 2:
        skipped.append(link)
        continue
    assert len(split) == 1

    # now split into [ empty string, <year>, <paper-id> ]
    split = split[0]
    paper_id = split.split("/")
    if len(paper_id) != 3:
        skipped.append(link)
        continue;

    paper_id = int(paper_id[2])
    if paper_id > last_paper_id:
        #print
        #print paper_id
        title, authors, abstract, pdflink = process_paper(url, paper_id, parser)
        new_last_paper_id = max(paper_id, new_last_paper_id)
            
        email_html += "\n"
        email_html += "<b>Title:</b> " + title + " (" + str(paper_id) + " <a href=\"" + pdflink + "\">PDF</a>)<br />\n";
        email_html += "<b>Authors:</b> " + authors + "<br />\n";
        email_html += "<b><a href=\"" + url + str(paper_id) + "\">Abstract</a>:</b> " + abstract + "<br /><br />\n";

        email_text += "\n"
        email_text += "Title: " + title + "\n";
        email_text += "Authors:  " + authors + "\n";
        email_text += "Link: " + pdflink + "\n";
        email_text += "Abstract: " + abstract + "\n\n";

# if there were new papers, email them to the right person
if new_last_paper_id > last_paper_id:
    email_html = email_html.encode('utf-8').strip()
    email_text = email_text.encode('utf-8').strip()

    print
    print "Emailing " + notified_email + ":"
    print
    print email_html
    print

    # craft MIME email
    mime_email = MIMEMultipart('alternative')
    mime_email['Subject'] = 'New Crypto ePrints: ' + str(year) + '/' + str(last_paper_id + 1)
    if new_last_paper_id > last_paper_id + 1:
        mime_email['Subject'] += ' to ' + str(year) + '/' + str(new_last_paper_id)
    mime_email['From'] = sender_gmail_addr;
    mime_email['To'] = notified_email;
    mime_email.attach(MIMEText(email_text, 'plain'))
    mime_email.attach(MIMEText(email_html, 'html'))

    # connect to Gmail and send
    if simulate_email == False:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_gmail_username, sender_gmail_passw);
        server.sendmail(
            sender_gmail_addr,
            notified_email,
            mime_email.as_string())
        server.quit()

        print "Sent email successfully to:", notified_email
    else:
        print "Simulating, so no email was sent."

    if simulate_conf_update == False:
        # write the new last paper ID in the conf file (and rewrite the same year)
        f.truncate(0)
        f.seek(0)
        f.write(str(year) + '\n')
        f.write(str(new_last_paper_id) + '\n')
        f.close()
        print "Wrote last ID to conf file:", new_last_paper_id
    else:
        print "Simulating so conf file was not updated"
