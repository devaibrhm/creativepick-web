import streamlit as st
import os.path
import re
import json
import urllib.parse
import io
import zipfile
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image

# ==========================================
# 1. KONFIGURASI & STYLE (DARK MODE, PORTRAIT & STICKY BAR)
# ==========================================
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
DB_FILE = "projects.json"
ADMIN_USER = "admin"
ADMIN_PASS = "playkamera123"
BASE_URL = "https://creativepick.streamlit.app"

def apply_custom_style():
    st.markdown("""
        <style>
        /* Base Theme */
        .stApp { background: linear-gradient(180deg, #0f0c29 0%, #302b63 50%, #24243e 100%); color: #ffffff; }
        
        /* Memberikan ruang kosong di paling bawah agar foto terakhir tidak tertutup Bar */
        .block-container { padding-bottom: 90px !important; }

        /* MENGHILANGKAN GAP ANTAR ELEMEN */
        [data-testid="column"] [data-testid="stVerticalBlock"] { gap: 0 !important; }
        [data-testid="column"] { padding: 5px !important; }

        /* IMAGE CONTAINER (PORTRAIT 2:3) */
        .img-container { position: relative; width: 100%; margin: 0; }
        .img-container img {
            aspect-ratio: 2 / 3 !important; object-fit: cover !important; width: 100% !important;
            border-radius: 12px 12px 0 0 !important; display: block;
            border: 1px solid rgba(255,255,255,0.1);
        }

        /* BAR NAMA FILE */
        .filename-bar {
            background-color: #0d0b21; color: white; text-align: center;
            font-size: 11px; padding: 6px 5px; width: 100%;
            border-left: 1px solid rgba(255,255,255,0.1); border-right: 1px solid rgba(255,255,255,0.1);
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }

        /* TOMBOL PILIH (ROUNDED BAWAH) */
        .pilih-btn-wrap { width: 100%; }
        .pilih-btn-wrap .stButton button {
            width: 100% !important; border-radius: 0 0 12px 12px !important;
            border: none !important; font-weight: bold; padding: 10px 0 !important;
        }
        .btn-purple button { background: linear-gradient(90deg, #8e2de2 0%, #4a00e0 100%) !important; color: white !important; }
        .btn-blue button { background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%) !important; color: white !important; }

        /* --- STICKY BOTTOM BAR KHUSUS MOBILE/WEB --- */
        .sticky-bottom-bar {
            position: fixed;
            bottom: 0; left: 0; width: 100%;
            background: rgba(15, 12, 41, 0.95);
            backdrop-filter: blur(10px);
            border-top: 1px solid #8e2de2;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 99999;
            box-shadow: 0 -5px 15px rgba(0,0,0,0.5);
        }
        .sticky-text {
            color: white; font-weight: bold; font-size: 15px; margin: 0;
        }
        .sticky-btn {
            background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
            color: white !important; text-decoration: none !important;
            padding: 10px 20px; border-radius: 25px;
            font-weight: bold; font-size: 14px;
            box-shadow: 0 4px 10px rgba(0, 210, 255, 0.3);
            transition: 0.3s;
        }
        .sticky-btn:hover { filter: brightness(1.1); transform: scale(1.05); }

        /* SIDEBAR STYLING */
        [data-testid="stSidebar"] { background-color: rgba(15, 12, 41, 0.95); border-right: 1px solid #4a00e0; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. SISTEM GOOGLE DRIVE & PROCESSING
# ==========================================
def get_gdrive_service():
    creds = None
    if "gdrive_token" in st.secrets:
        token_data = json.loads(st.secrets["gdrive_token"])
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    elif os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            st.error("Kunci Akses Google Drive tidak valid!")
            st.stop()
            
    return build('drive', 'v3', credentials=creds)

@st.cache_data(show_spinner=False, ttl=3600)
def get_processed_image(file_id):
    try:
        service = get_gdrive_service()
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        return Image.open(fh)
    except Exception as e:
        return None

def manage_db(action="read", name=None, fid=None):
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({}, f)
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
        
    if action == "write":
        data[name] = fid
        with open(DB_FILE, 'w') as f:
            json.dump(data, f)
    return data

# ==========================================
# 3. HALAMAN CLIENT (DENGAN STICKY BAR)
# ==========================================
def page_client(folder_id):
    apply_custom_style()
    
    if 'pilihan' not in st.session_state: 
        st.session_state['pilihan'] = []

    st.sidebar.title("📋 Konfirmasi")
    txt_pilihan = "\n".join(st.session_state['pilihan'])
    st.sidebar.text_area("File terpilih:", value=txt_pilihan, height=250)
    
    pesan_wa = urllib.parse.quote(f"Halo Playkamera! Ini list foto pilihan saya:\n\n{txt_pilihan}")

    if st.session_state.get("logged_in"):
        if st.button("⬅️ Dashboard"):
            st.query_params.clear()
            st.rerun()

    st.title("📸 Creative.pick")

    service = get_gdrive_service()
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false",
            pageSize=100, fields="files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            st.warning("⚠️ Folder kosong.")
        else:
            col_a, col_b = st.columns([3, 1])
            with col_a: 
                st.write("Silakan pilih foto terbaik Anda.")
            with col_b: 
                if st.button("Reset"):
                    st.session_state['pilihan'] = []
                    st.rerun()

            cols = st.columns(2)
            for idx, item in enumerate(items):
                with cols[idx % 2]:
                    st.markdown('<div class="img-container">', unsafe_allow_html=True)
                    img_data = get_processed_image(item['id'])
                    if img_data: 
                        st.image(img_data, width="stretch")
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown(f'<div class="filename-bar">{item["name"]}</div>', unsafe_allow_html=True)

                    is_sel = item['name'] in st.session_state['pilihan']
                    label = "✓ DIPILIH" if is_sel else "PILIH"
                    btn_class = "btn-blue" if is_sel else "btn-purple"

                    st.markdown(f'<div class="pilih-btn-wrap {btn_class}">', unsafe_allow_html=True)
                    if st.button(label, key=f"s_{item['id']}"):
                        if is_sel: 
                            st.session_state['pilihan'].remove(item['name'])
                        else: 
                            st.session_state['pilihan'].append(item['name'])
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                    
            sticky_html = f"""
            <div class="sticky-bottom-bar">
                <div class="sticky-text">✅ Terpilih: {len(st.session_state['pilihan'])}/100</div>
                <a href="https://wa.me/628xxx?text={pesan_wa}" class="sticky-btn" target="_blank">🚀 Kirim WA</a>
            </div>
            """
            st.markdown(sticky_html, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error: {e}")

# ==========================================
# 4. HALAMAN ADMIN (DASHBOARD)
# ==========================================
def page_admin():
    apply_custom_style()
    if "logged_in" not in st.session_state: 
        st.session_state["logged_in"] = False
    
    if not st.session_state["logged_in"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div style="background:rgba(255,255,255,0.05); padding:25px; border-radius:15px; border:1px solid #8e2de2">', unsafe_allow_html=True)
            st.header("🔐 Admin Login")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Masuk"):
                if u == ADMIN_USER and p == ADMIN_PASS:
                    st.session_state["logged_in"] = True
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        return

    st.title("👨‍💻 Dashboard Fotografer")
    st.sidebar.button("Log Out", on_click=lambda: st.session_state.update({"logged_in": False}))
    
    st.sidebar.divider()
    st.sidebar.header("📥 Download Project")
    dl_folder_id = st.sidebar.text_input("ID Folder Project", placeholder="Paste Folder ID GDrive")
    dl_list_names = st.sidebar.text_area("Paste List Nama File dari Client", help="Pisahkan dengan baris baru")
    
    if st.sidebar.button("Generate Download ZIP"):
        if dl_folder_id and dl_list_names:
            service = get_gdrive_service()
            file_names = [n.strip() for n in dl_list_names.split("\n") if n.strip()]
            zip_buffer = io.BytesIO()
            files_found = 0
            
            with st.sidebar.status("Sedang memproses file...", expanded=True) as status:
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for name in file_names:
                        q = f"name = '{name}' and '{dl_folder_id}' in parents and trashed = false"
                        res = service.files().list(q=q, fields="files(id, name)").execute().get('files', [])
                        if res:
                            file_id = res[0]['id']
                            request = service.files().get_media(fileId=file_id)
                            fh = io.BytesIO()
                            downloader = MediaIoBaseDownload(fh, request)
                            done = False
                            while not done: 
                                _, done = downloader.next_chunk()
                            zip_file.writestr(res[0]['name'], fh.getvalue())
                            files_found += 1
                            st.write(f"✅ Diambil: {res[0]['name']}")
                        else:
                            st.write(f"❌ Gagal: {name}")
                status.update(label=f"Selesai! {files_found} file dikemas.", state="complete")

            if files_found > 0:
                zip_buffer.seek(0)
                st.sidebar.download_button(
                    label="💾 Download ZIP Sekarang", data=zip_buffer,
                    file_name="pilihan_client.zip", mime="application/zip", use_container_width=True
                )
            else: 
                st.sidebar.error("File tidak ditemukan.")

    tab1, tab2 = st.tabs(["➕ Buat Project", "📂 Riwayat"])
    with tab1:
        c_name = st.text_input("Nama Client")
        g_url = st.text_input("Link Folder GDrive")
        if st.button("Buat Project"):
            fid = re.search(r'folders/([\w-]+)', g_url)
            fid = fid.group(1) if fid else g_url
            if c_name and fid:
                manage_db("write", c_name, fid)
                st.success("Link berhasil dibuat!")
                st.code(f"{BASE_URL}/?folder={fid}")

    with tab2:
        projects = manage_db()
        for name, fid in projects.items():
            with st.expander(f"📁 {name}"):
                st.write(f"ID: `{fid}`")
                if st.button(f"Lihat Project {name}", key=f"v_{fid}"):
                    st.query_params["folder"] = fid
                    st.rerun()

# ==========================================
# 5. RUNNER
# ==========================================
if __name__ == "__main__":
    fid_param = st.query_params.get("folder")
    if fid_param: 
        page_client(fid_param)
    else: 
        page_admin()