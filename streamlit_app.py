import streamlit as st
from supabase import create_client
from datetime import date
import os, smtplib, hmac
from email.message import EmailMessage

st.set_page_config(page_title='Mana Catering', page_icon='🍽️', layout='wide')
LOCATIONS = [x.strip() for x in st.secrets.get('LOCATIONS', 'Narasaraopet Town,Narasaraopet Rural,Ravipadu,Petta,Yellamanda,Other nearby village').split(',') if x.strip()]
CATEGORIES = ['Wedding & function catering', 'Traditional cooking team', 'Home chef', 'Veg catering', 'Non-veg catering']

@st.cache_resource
def db():
    url = st.secrets.get('SUPABASE_URL', '')
    key = st.secrets.get('SUPABASE_SERVICE_ROLE_KEY', '')
    if not url or not key:
        return None
    return create_client(url, key)

client = db()

def notify(subject, body):
    required = ['SMTP_HOST','SMTP_USER','SMTP_PASSWORD','SMTP_FROM','ADMIN_EMAIL']
    if not all(st.secrets.get(k, '') for k in required):
        return
    try:
        msg=EmailMessage(); msg['Subject']=subject; msg['From']=st.secrets['SMTP_FROM']; msg['To']=st.secrets['ADMIN_EMAIL']; msg.set_content(body)
        with smtplib.SMTP(st.secrets['SMTP_HOST'], int(st.secrets.get('SMTP_PORT',587)), timeout=15) as s:
            s.starttls(); s.login(st.secrets['SMTP_USER'],st.secrets['SMTP_PASSWORD']); s.send_message(msg)
    except Exception:
        # Submission should still be saved even if optional email fails.
        pass

def ready():
    if client is None:
        st.error('Database is not configured yet. Follow DEPLOYMENT.md to add Supabase secrets in Streamlit Community Cloud.')
        return False
    return True

st.title('🍽️ Mana Catering')
st.caption('Find local catering teams and traditional cooks around Narasaraopet.')
if client is None:
    st.warning('Deployment setup required: connect a Supabase database using Streamlit secrets. See DEPLOYMENT.md.')

browse, register, admin = st.tabs(['Find catering', 'Register your team', 'Admin'])
with browse:
    st.subheader('Explore approved providers')
    c1,c2=st.columns(2)
    with c1: loc=st.selectbox('Choose your village / town', LOCATIONS)
    with c2: cat=st.selectbox('Catering type', ['All categories']+CATEGORIES)
    if ready():
        try:
            q=client.table('providers').select('*').eq('status','approved').eq('location',loc)
            if cat!='All categories': q=q.eq('category',cat)
            rows=q.order('created_at', desc=True).execute().data or []
            if not rows: st.info('No approved providers listed here yet. You can invite a local catering team to register.')
            for p in rows:
                with st.container(border=True):
                    left,right=st.columns([4,1])
                    with left:
                        st.markdown('### '+p['name'])
                        st.write(f"**{p['category']}** · {p['location']}")
                        if p.get('specialties'): st.write('Specialties: '+p['specialties'])
                        if p.get('capacity'): st.write('Capacity: '+p['capacity'])
                        if p.get('price'): st.write('Indicative price: '+p['price'])
                        if p.get('description'): st.write(p['description'])
                    with right:
                        phone=''.join(ch for ch in p['phone'] if ch.isdigit() or ch=='+')
                        st.link_button('📞 Call', 'tel:'+phone, use_container_width=True)
                        st.caption('Confirm price, availability and service details directly.')
                    with st.expander('Send an enquiry'):
                        with st.form('enq_'+str(p['id'])):
                            n=st.text_input('Your name'); ph=st.text_input('Your phone'); event=st.text_input('Event type (e.g. wedding)'); when=st.date_input('Event date', value=date.today()); guests=st.text_input('Expected guests'); budget=st.text_input('Budget (optional)'); notes=st.text_area('Additional details')
                            ok=st.form_submit_button('Submit enquiry')
                        if ok:
                            if len(n.strip())<2 or len(ph.strip())<7 or not event.strip(): st.error('Enter your name, valid phone number and event type.')
                            else:
                                try:
                                    client.table('enquiries').insert({'provider_id':p['id'],'customer_name':n.strip(),'phone':ph.strip(),'location':loc,'event_type':event.strip(),'event_date':str(when),'guests':guests,'budget':budget,'notes':notes}).execute()
                                    notify('Mana Catering: new customer enquiry',f"Provider: {p['name']}\nCustomer: {n}\nPhone: {ph}\nEvent: {event}\nDate: {when}\nGuests: {guests}\nBudget: {budget}\nNotes: {notes}")
                                    st.success('Enquiry submitted. The team will be contacted through the details provided.')
                                except Exception as e: st.error('Could not submit enquiry. Please try again later.')
        except Exception: st.error('Could not load providers. Check your Supabase setup and table permissions.')

with register:
    st.subheader('List your catering team')
    st.write('Your listing will be reviewed by the Mana Catering admin before it appears publicly. Your phone number is published only with your consent.')
    with st.form('provider_form'):
        name=st.text_input('Team / provider name *'); phone=st.text_input('Contact phone *'); location=st.selectbox('Village / town *',LOCATIONS,key='reg_loc'); category=st.selectbox('Catering type *',CATEGORIES); specialties=st.text_input('Specialties (optional)'); capacity=st.text_input('Capacity (e.g. 100–300 people)'); price=st.text_input('Indicative price (optional)'); description=st.text_area('About your service'); consent=st.checkbox('I own or am authorized to share this phone number, and I agree to its publication if approved. *'); submit=st.form_submit_button('Submit for approval')
    if submit:
        if not ready(): pass
        elif len(name.strip())<2 or len(phone.strip())<7 or not consent: st.error('Please complete required fields and provide consent.')
        else:
            try:
                data={'name':name.strip(),'phone':phone.strip(),'location':location,'category':category,'specialties':specialties.strip(),'capacity':capacity.strip(),'price':price.strip(),'description':description.strip(),'consent':True,'status':'pending'}
                result=client.table('providers').insert(data).execute()
                notify('Mana Catering: provider awaiting approval',f"New provider: {name}\nPhone: {phone}\nLocation: {location}\nCategory: {category}")
                st.success('Submitted successfully. Your listing is pending admin review.')
            except Exception: st.error('Submission failed. Please check your connection and try again.')

with admin:
    st.subheader('Admin review')
    if not ready(): st.stop()
    if not st.session_state.get('admin_ok'):
        with st.form('admin_login'):
            u=st.text_input('Admin username'); pw=st.text_input('Admin password',type='password'); login=st.form_submit_button('Sign in')
        if login:
            expected_u=st.secrets.get('ADMIN_USERNAME',''); expected_p=st.secrets.get('ADMIN_PASSWORD','')
            if expected_u and expected_p and hmac.compare_digest(u,expected_u) and hmac.compare_digest(pw,expected_p): st.session_state.admin_ok=True; st.rerun()
            else: st.error('Invalid admin credentials.')
    else:
        if st.button('Sign out'): st.session_state.admin_ok=False; st.rerun()
        try:
            pending=client.table('providers').select('*').eq('status','pending').order('created_at').execute().data or []
            st.write(f'**Pending submissions: {len(pending)}**')
            for p in pending:
                with st.container(border=True):
                    st.markdown('### '+p['name']); st.write(f"{p['phone']} · {p['location']} · {p['category']}"); st.write(p.get('description',''))
                    a,b=st.columns(2)
                    with a:
                        if st.button('Approve',key='a'+str(p['id']),type='primary'):
                            client.table('providers').update({'status':'approved'}).eq('id',p['id']).execute(); st.success('Approved'); st.rerun()
                    with b:
                        if st.button('Reject',key='r'+str(p['id'])):
                            client.table('providers').update({'status':'rejected'}).eq('id',p['id']).execute(); st.warning('Rejected'); st.rerun()
            with st.expander('Recent customer enquiries'):
                enquiries=client.table('enquiries').select('*').order('created_at',desc=True).limit(100).execute().data or []
                if not enquiries: st.info('No enquiries yet.')
                for e in enquiries: st.write(f"**{e['customer_name']}** · {e['phone']} · {e['event_type']} · {e.get('event_date','')} · Provider ID {e['provider_id']} — {e.get('notes','')}")
        except Exception: st.error('Admin data could not be loaded. Verify Supabase table setup.')

st.divider()
st.caption('Mana Catering is a discovery platform. Customers should independently confirm provider identity, food practices, pricing and availability.')
