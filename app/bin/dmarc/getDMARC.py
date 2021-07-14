import os, zipfile, gzip, shutil, re
from pathlib import Path
from datetime import datetime, timedelta
import pytz

#this depends on exchangelib https://github.com/ecederstrand/exchangelib 
from exchangelib import DELEGATE, IMPERSONATION, Account, Credentials, EWSDateTime, EWSTimeZone, Configuration, NTLM, GSSAPI, CalendarItem, Message, Mailbox, Attendee, Q, ExtendedProperty, FileAttachment, ItemAttachment, HTMLBody, Build, Version, FolderCollection

#Configure Credentials
#Depending on your O365 tenant configuration, you will need to use 
#"<dmarc-rua-mailbox>@<tenant>.onmicrosoft.com" or "<dmarc-rua-mailbox>@<domain>.<tld>" as the username.

credentials = Credentials(username='dmarc-rua@<tenant>.onmicrosoft.com', password='<change me>')
# If you want to enable the fault tolerance, create credentials as a service account instead:
#credentials = ServiceAccount(username='dmarc-rua@<domain>.<tld>', password='<change me>')

config = Configuration(server='outlook.office365.com', credentials=credentials)
account = Account(primary_smtp_address='dmarc-rua@<domain>.<tld>', config=config, autodiscover=False, access_type=DELEGATE)

#define processing directories
d = '/app/dat/dmarc/zipped'
de = '/app/dat/dmarc/extracted/'
da = '/app/dat/dmarc/archive/'
dp = '/app/dat/dmarc/parsed/'
ds = '/app/dat/dmarc/siem/'

for item in (account.inbox / 'rua').all().order_by('-datetime_received')[:100]:
	for attachment in item.attachments:
		if isinstance(attachment, FileAttachment):
			local_path = os.path.join(d, attachment.name)
			if(attachment.name.endswith('.gz') or attachment.name.endswith('.zip')):
				with open(local_path, 'wb') as f, attachment.fp as fp:
					buffer = fp.read(1024)
					while buffer:
						f.write(buffer)
						buffer = fp.read(1024)
				print('Saved attachment to', local_path)
	item.move(account.inbox / 'ingested')
	#print(item.subject, item.sender, item.datetime_received)

#remove zip files over 1mb to limit damage from oversized attachments being sent to public mailbox
max_attachment_size = 1000000 #1mb
for dirName, subdirList, fileList in os.walk(d):
    for fname in fileList:
        if os.path.getsize(d+'/'+fname) > max_attachment_size:
            os.remove(d+'/'+fname)

			
#cleanup folders to prevent sumo from ingesting twice
for dirName, subdirList, fileList in os.walk(de):
    for fname in fileList:
        if os.path.exists(de+'/'+fname):
            os.remove(de+'/'+fname)

for dirName, subdirList, fileList in os.walk(dp):
    for fname in fileList:
		os.remove(dp+'/'+fname)

for dirName, subdirList, fileList in os.walk(ds):
    for fname in fileList:
		os.remove(ds+'/'+fname)
		
		
#File processing to unzip and archive files			
for dirName, subdirList, fileList in os.walk(d):
    for fname in fileList:
		print(d+'/'+fname)
		if(fname.endswith('.zip')):
			with zipfile.ZipFile(d+'/'+fname, 'r') as zip_ref:
				zip_ref.extractall(de)
				os.rename(d+'/'+fname,da+fname+'.zip')
		if(fname.endswith('.gz')):
			with gzip.open(d+'/'+fname, 'rb') as f_in:
				with open(de+fname.replace(".gz",""), 'wb') as f_out:
					shutil.copyfileobj(f_in, f_out)
					os.rename(d+'/'+fname,da+fname+'.gz')

#parsing to remove whitespace and newlines
for dirName, subdirList, fileList in os.walk(de):
	for fname in fileList:
		if os.path.exists(de+fname):
			clean = open(de+fname).read().replace('  ', '').replace('\t', '').replace('\n', '').replace('\r','')
			f = open(dp+fname, 'w')
			f.write(clean)
			f.close()
			os.remove(de+fname)
		
#parsing to make more Sumo Compliant
for dirName, subdirList, fileList in os.walk(dp):
	for fname in fileList:
		data = open(dp+fname).read()
		
		dmarc_version_re = re.compile("(<version>.*?<\/version>)")
		if(dmarc_version_re.search(data)):
			dmarc_version = dmarc_version_re.search(data).group(1)
		else:
			dmarc_version = ''
			
		rec_meta_re = re.compile("(<report_metadata>.*?<\/report_metadata>)")
		if(rec_meta_re.search(data)):
			rec_meta = rec_meta_re.search(data).group(1)
		else:
			rec_meta = ''
		
		xml_header_re = re.compile("(<\?xml.*?>)")
		if(xml_header_re.search(data)):
			xml_header = xml_header_re.search(data).group(1)
		else:
			xml_header = ''
		
		dmarc_pub_policy_re = re.compile("(<policy_published>.*?<\/policy_published>)")
		dmarc_pub_policy = dmarc_pub_policy_re.search(data).group(1)
		sumo_data = data.replace(xml_header,'').replace(dmarc_pub_policy,'').replace(rec_meta,'').replace('<record>', xml_header+'<record>'+rec_meta+dmarc_pub_policy).replace('</record>','</record>\n').replace('<feedback>','').replace('</feedback>','').replace(dmarc_version,'')
		#remove initial xml header, report_meta, and policy_published
		f = open(ds+fname, 'w')
		f.write(sumo_data)
		f.close()
		#os.remove(dp+fname)
