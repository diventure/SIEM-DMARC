# SIEM-DMARC
DMARC SIEM Ingestion and Dashboards for SumoLogic 

# Requirements
- Python 3.x
- Exchangelib https://github.com/ecederstrand/exchangelib
- Various Python Libraries to install using PIP

# Notes
- Create dmarc-rua email box like dmarc-rua@company.tld and dmarc-ruf@company.tld
- Must configure DNS to send RUA to an exchange email box
  - https://dmarc.org/overview/
    - "v=DMARC1;p=none;pct=100;rua=mailto:dmarc-rua@company.tld"
  - Don't forget External Destination Verification if needed for multiple domains
    - https://dmarcian.com/what-is-external-destination-verification/
- Uses Exchangelib to download RUA emails
- Python script uses a series of folders to extract, parse, and import data from Exchange to SumoLogic
- This is designed to be on a server dedicated for SumoLogic Ingest Processing
  - All SumoLogic Apps are designed to be run from /app base folder
  - Please modify configurations and folder structure to fit your needs
- This script can be used to ingest to any SIEM, but this use case is for SumoLogic


# Configuration
1) In getDMARC.py change credentials to fit your o365 configuration requirements
2) In getDMARC.py change processing directories to fit your server or create folders as defined "/app/dat/dmarc/\<stage\>"
3) In o365 RUA Email Box create folders "rua" and "ingested"
4) In O365 RUA Email box create a rule to move new dmarc reports to the "rua" folder.
- This is to prevent spam from being processed from the root directory.  
- This is also where you can choose not to process from certain senders like LinkedIn autoreply failures
5) Configure SumoLogic Collector to collect from '/app/dat/dmarc/siem/' (or whatever you set "ds" equal to getDMARC.py)


# Dashboards
1) Change "\<srccat\>" to whatever source category you use
2) then change "\<domain\>" to your domains
2) Import into SumoLogic
