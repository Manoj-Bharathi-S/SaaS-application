import streamlit as st
import requests
import json
import base64

# Services
KMS_URL = "http://localhost:8005"
CHAIN_URL = "http://localhost:8006"
ML_URL = "http://localhost:8007"
ENC_URL = "http://localhost:8001"
PROXY_URL = "http://localhost:8002"
ACCESS_URL = "http://localhost:8008"

st.set_page_config(layout="wide", page_title="Secure Cloud Storage")

st.title("Secure Cloud Storage Dashboard")

tab1, tab2, tab3 = st.tabs(["Blockchain Audit", "File Sharing", "Admin & ML"])

# --- TAB 1: AUDIT ---
with tab1:
    st.header("Immutable Audit Ledger")
    try:
        if st.button("Refresh Chain"):
            pass
        response = requests.get(f"{CHAIN_URL}/chain")
        if response.status_code == 200:
            chain_data = response.json()
            st.write(f"Chain Height: {chain_data['length']}")
            
            for block in chain_data['chain']:
                with st.expander(f"Block #{block['index']} - {block['hash'][:10]}..."):
                    st.json(block)
        else:
            st.error("Failed to fetch blockchain")
    except Exception as e:
        st.error(f"Blockchain Service Unreachable: {e}")

# --- TAB 2: SHARING ---
with tab2:
    st.header("Secure File Sharing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Encrypt & Upload")
        f = st.file_uploader("Choose file")
        if f and st.button("Encrypt"):
            try:
                content = f.read()
                b64_content = base64.b64encode(content).decode('utf-8')
                
                payload = {
                    "plaintext": b64_content,
                    "meta": {"filename": f.name, "owner": "alice"}
                }
                r = requests.post(f"{ENC_URL}/encrypt", json=payload)
                if r.status_code == 200:
                    data = r.json()
                    st.success("File Encrypted!")
                    st.code(json.dumps(data, indent=2))
                    st.session_state['last_cipher'] = data['cipher']
                    st.session_state['last_key_id'] = data['key_id']
                    st.session_state['last_filename'] = f.name
                else:
                    st.error(f"Encryption Failed: {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        st.subheader("2. Share (Re-Key)")
        target_user = st.text_input("Share with (email)", "bob@company.com")
        if st.button("Generate Re-Key"):
             try:
                r = requests.post(f"{PROXY_URL}/gen_rekey", json={"from_user": "alice", "to_user": target_user})
                if r.status_code == 200:
                    st.success("Re-Key Generated")
                    st.json(r.json())
                    st.session_state['last_rekey_id'] = r.json()['rekey_id']
                else:
                    st.error(f"Failed: {r.text}")
             except Exception as e:
                 st.error(f"Error: {e}")
                 
        st.subheader("3. Download (Re-Encrypt)")
        rk_id = st.text_input("Re-Key ID", st.session_state.get('last_rekey_id', ''))
        cipher = st.text_area("Cipher Blob", st.session_state.get('last_cipher', ''))
        
        if st.button("Download & Re-Encrypt"):
            try:
                payload = {"cipher_blob": cipher, "rekey_id": rk_id}
                r = requests.post(f"{PROXY_URL}/reencrypt", json=payload)
                if r.status_code == 200:
                     st.success("Re-Encryption Success! (User can now decrypt)")
                     st.text(r.json()['cipher_re'][:100] + "...")
                     re_cipher = r.json()['cipher_re']
                     st.session_state['dec_input'] = re_cipher
                     st.download_button("Download Re-Encrypted File", re_cipher, "reencrypted_data.txt")
                elif r.status_code == 403:
                    st.error("ACCESS DENIED: Proxy refused re-encryption.")
                else:
                    st.error(f"Failed: {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")

        st.subheader("4. Decrypt (Bob)")
        dec_cipher = st.text_area("Encrypted Content", st.session_state.get('dec_input', st.session_state.get('last_cipher', '')), key='dec_cipher')
        dec_key_id = st.text_input("Key ID", st.session_state.get('last_key_id', ''), key='dec_key')
        
        if st.button("Decrypt File"):
            try:
                # Sanitize inputs (remove whitespace/newlines from copy-paste)
                clean_cipher = dec_cipher.strip()
                clean_key_id = dec_key_id.strip()
                
                payload = {"cipher": clean_cipher, "key_id": clean_key_id}
                r = requests.post(f"{ENC_URL}/decrypt", json=payload)
                if r.status_code == 200:
                    try:
                        pt_b64 = r.json()['plaintext']
                        pt_bytes = base64.b64decode(pt_b64)
                        st.success("File Decrypted Successfully!")
                        file_name = st.session_state.get('last_filename', 'decrypted_file.bin')
                        st.download_button("Download Original File", pt_bytes, file_name)
                        st.text_area("Decrypted Content Preview", pt_bytes.decode('utf-8', errors='ignore'))
                    except Exception as e:
                         st.error(f"Decoding Error: {e}")
                else:
                    st.error(f"Decryption Failed: {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")

# --- TAB 3: ADMIN ---
with tab3:
    st.header("Admin & ML Status")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("ML Anomaly Detector")
        try:
             r = requests.get(f"{ML_URL}/health")
             st.json(r.json())
        except:
            st.error("ML Service Down")
            
        if st.button("Train Model"):
            requests.post(f"{ML_URL}/train", json={"contamination": 0.05})
            st.success("Model Retrained")

    with col2:
        st.subheader("Access Control")
        user_to_revoke = st.text_input("Revoke User")
        if st.button("Revoke"):
            requests.post(f"{ACCESS_URL}/revoke", json={"username": user_to_revoke})
            st.warning(f"User {user_to_revoke} revoked!")

