"""Interactive setup: passwords never appear in shell history or output."""
import sys,json,secrets,getpass
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from services.access_control import ROLES,password_hash

if __name__=='__main__':
    username=input('Username: ').strip().casefold()
    role=input('Role (Admin / Analyst / Executive / Viewer): ').strip()
    if not username or role not in ROLES:raise SystemExit('Provide a username and supported role.')
    password=getpass.getpass('Password (at least 12 characters): ')
    if len(password)<12 or password!=getpass.getpass('Confirm password: '):raise SystemExit('Passwords must match and contain at least 12 characters.')
    path=ROOT/'.streamlit/accounts.json'
    accounts=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    if username in accounts:raise SystemExit('Account already exists. Use a different username or manage the private account file.')
    salt=secrets.token_hex(16)
    accounts[username]={'salt':salt,'password_hash':password_hash(password,salt),'role':role}
    path.write_text(json.dumps(accounts,indent=2),encoding='utf-8')
    print('Private hashed account created. Set SUPPLYCHAIN_AUTH_MODE=accounts in your private .env and restart.')
