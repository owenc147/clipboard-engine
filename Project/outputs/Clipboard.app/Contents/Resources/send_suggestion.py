"""Gmail submission. Secrets arrive only on stdin; never print credentials."""
import json,sys,smtplib,ssl
from email.message import EmailMessage
from email.utils import formatdate
RECIPIENT='ofc14700@gmail.com'
SUBJECT='BINOCULAR SUGGESTION'
def deliver(data):
    smtp=None
    try:
        password=data.get('password','')
        if not password: return {'ok':False,'status':'Gmail is not connected.'}
        smtp=smtplib.SMTP_SSL('smtp.gmail.com',465,timeout=25,context=ssl.create_default_context())
        smtp.login(RECIPIENT,password)
        if data.get('mode')=='verify':return {'ok':True,'status':'Gmail connected.'}
        text=data.get('text','').strip()
        if not text or len(text)>4000:return {'ok':False,'status':'Suggestion must contain 1–4,000 characters.'}
        msg=EmailMessage();msg['From']=RECIPIENT;msg['To']=RECIPIENT;msg['Subject']=SUBJECT;msg['Date']=formatdate(localtime=True)
        msg.set_content('Category: '+data.get('category','Idea')+'\nSubmitted: '+data.get('created','')+'\nSuggestion ID: '+data.get('id','')+'\n\n'+text)
        rejected=smtp.send_message(msg,from_addr=RECIPIENT,to_addrs=[RECIPIENT])
        if rejected:return {'ok':False,'status':'Gmail rejected the recipient. Saved locally.'}
        return {'ok':True,'status':'Sent · accepted by Gmail'}
    except smtplib.SMTPAuthenticationError:return {'ok':False,'status':'Gmail sign-in failed. Reconnect using a Gmail app password.'}
    except smtplib.SMTPResponseException:return {'ok':False,'status':'Gmail rejected this request. Saved locally; try again later.'}
    except Exception:return {'ok':False,'status':'Delivery not confirmed. Check your inbox before retrying to avoid duplicates.'}
    finally:
        if smtp:
            try:smtp.quit()
            except Exception:pass
if __name__=='__main__':
    try:result=deliver(json.load(sys.stdin))
    except Exception:result={'ok':False,'status':'Email request could not be processed.'}
    print(json.dumps(result))
