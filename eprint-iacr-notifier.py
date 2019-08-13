#!/usr/bin/env python2.7

from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pprint import pprint

import bs4
import datetime
import smtplib
import sys
import urllib2

def get_url(url):
    print "Downloading page at", url, "...",
    response = urllib2.urlopen(url)
    html = response.read()
    print " Done."
    return html

def dedup_spaces(string):
    return u" ".join(string.split()).strip()

# paper IDs in URLs need to be padded with zeros
# e.g., 1 should be 001
def format_paper_id(paper_id):
    if paper_id >= 100:
        return str(paper_id)
    else:
        return "{:03d}".format(paper_id)

def process_paper(base_url, paper_id, parser):
    url = base_url + format_paper_id(paper_id)
    paper_html = get_url(url)

    soup = BeautifulSoup(paper_html, parser)

    bs = soup.find_all('b')
    title = bs[0].text
    authors = soup.find('i')
    
    title = dedup_spaces(title)
    authors = dedup_spaces(authors.text)

    # For some papers, after <b>Abstract:</b> there could be tags like <p /> in the abstract itself (see https://eprint.iacr.org/2019/868 for example).
    # This means bs[1].next_sibling won't get the full abstract, so we have to keep iterating.
    first_paragraph = bs[1].next_sibling
    # first_paragraph.parent is the <body> tag
    # bs[1] is a Tag object and bs[1].next_sibling is a NavigableString

    assert(type(first_paragraph) is bs4.element.NavigableString)
    abstract = dedup_spaces(first_paragraph)

    curr_paragraph = first_paragraph.next_sibling
    while True:  # the next <b> tag is for "Category / Keywords"
        assert(type(first_paragraph) is bs4.element.NavigableString or type(first_paragraph) is bs4.element.Tag)

        if type(curr_paragraph) is bs4.element.Tag:
            par = dedup_spaces(curr_paragraph.get_text())
        elif type(curr_paragraph) is bs4.element.NavigableString:
            par = dedup_spaces(curr_paragraph)
        else:
            print "ERROR: I need to better understand BeautifoulSoup"
            sys.exit(1)

        if par == "Category / Keywords:":
            break

        if len(par) > 0:
            assert(type(par) is unicode)
            abstract += u"\n\n" + par

        curr_paragraph = curr_paragraph.next_sibling

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

# delete's the script's name
script_name = sys.argv[0]
del sys.argv[0]

if len(sys.argv) < 4:
    print "Usage:", script_name, "<notified-email-address[,extra addresses]> <sender-Gmail-address> <sender-Gmail-password> <conf-file> [<only-simulate-email>] [<do-not-update-conf>]"
    sys.exit(1)

notified_email = sys.argv[0]
del sys.argv[0]
sender_gmail_addr = sys.argv[0]
sender_gmail_username = sender_gmail_addr.split("@")[0]
del sys.argv[0]
sender_gmail_passw = sys.argv[0]
del sys.argv[0]
conf_file = sys.argv[0]
del sys.argv[0]

now = datetime.datetime.now()
print "Time:", now.strftime("%Y-%m-%d %H:%M")

# please set to true when you are debugging and you don't want to send emails
simulate_email=False
# please set to true when you are debugging and you don't want to update the conf file with the latest paper ID
simulate_conf_update=False

if len(sys.argv) > 0:
    simulate_email=(sys.argv[0].lower() == "true" or sys.argv[0] == "1")
    del sys.argv[0]
    print "Simulate email sending?", simulate_email

    if len(sys.argv) > 0:
        simulate_conf_update=(sys.argv[0].lower() == "true" or sys.argv[0] == "1")
        del sys.argv[0]
        print "Do NOT update conf?", simulate_conf_update

    print

if simulate_email == False:
    test_gmail(sender_gmail_username, sender_gmail_passw)

parser = "lxml"

# open file for both reading and writing
f = open(conf_file, "r+")
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
email_html=u"Hey there,<br /><br />\nNew papers have been published on the Cryptology ePrint Archive!<br /><br />\n"
email_text=u"Hey there,\n\nNew papers have been published on the Cryptology ePrint Archive!\n\n"
firstPaper = True
for link in reversed(soup.find_all('a')):
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
        #print "Skipped non-paper link: " + link
        skipped.append(link)
        continue;

    paper_id = int(paper_id[2])
    if paper_id > last_paper_id:
        #print
        #print paper_id
        title, authors, abstract, pdflink = process_paper(url, paper_id, parser)
        new_last_paper_id = max(paper_id, new_last_paper_id)
            
        email_html += u"\n"
        if firstPaper == False:
            email_html += u"<hr /><br />\n"
        email_html += u"<b>Title:</b> " + title + " (" + format_paper_id(paper_id) + " <a href=\"" + pdflink + "\">PDF</a>)<br />\n"
        email_html += u"<b>Authors:</b> " + authors + "<br />\n"
        email_html += u"<b><a href=\"" + url + format_paper_id(paper_id) + "\">Abstract</a>:</b> " + abstract.replace("\n\n", "<br /><br />\n\n") + "<br /><br />\n"

        email_text += u"\n"
        email_text += u"Title: " + title + "\n"
        email_text += u"Authors:  " + authors + "\n"
        email_text += u"Link: " + pdflink + "\n"
        email_text += u"Abstract: " + abstract + "\n\n"
        email_text += u"-----------------"
        email_text += u"\n\n"

        firstPaper = False


# if there were new papers, email them to the right person
if new_last_paper_id > last_paper_id:
    email_text += u"Cheers,\nThe Crypto eprint whisperer\nhttps://github.com/alinush/eprint-iacr-notifier\n\nMay Alice and Bob forever talk securely."

    email_html += u"\n"
    email_html += u"Cheers,<br />\nThe Crypto eprint whisperer<br/>\n"
    email_html += u"GitHub: <a href=\"https://github.com/alinush/eprint-iacr-notifier\">https://github.com/alinush/eprint-iacr-notifier</a><br /><br/>\n"
    email_html += u"<i>May the hardness of discrete log forever be with you.</i>"

    email_html = email_html.strip()
    email_text = email_text.strip()

    print
    print "Emailing " + notified_email + ":"
    print
    # Must encode to UTF8 before printing. Otherwise some Unicode strings will print fine to stdout, but not when redirected to a file.
    print email_html.encode('utf-8')
    print

    # craft MIME email
    mime_email = MIMEMultipart('alternative')
    subj = 'New Crypto ePrints: ' + str(year) + '/' + format_paper_id(last_paper_id + 1)
    # WARNING: Updating mime_email['Subject'] with += or setting it twice with = results in two different subjects for the same email
    # when we notify two email addresses. This is why we only set it once with an if statement.
    if new_last_paper_id > last_paper_id + 1:
        mime_email['Subject'] = subj + ' to ' + str(year) + '/' + format_paper_id(new_last_paper_id)
    else:
        mime_email['Subject'] = subj
    mime_email['From'] = sender_gmail_addr;
    mime_email['To'] = notified_email;
    mime_email.attach(MIMEText(email_text, 'plain', 'utf-8'))
    mime_email.attach(MIMEText(email_html, 'html', 'utf-8'))

    # connect to Gmail and send
    if simulate_email == False:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_gmail_username, sender_gmail_passw);
        server.sendmail(
            sender_gmail_addr,
            notified_email.split(","),
            mime_email.as_string())
        server.quit()

        print "Sent email with title '" + mime_email['Subject'] + "' successfully to:", notified_email
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
