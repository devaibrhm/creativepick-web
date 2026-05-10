import streamlit as st
import os.path
import re
import json
import urllib.parse
import io
import zipfile
import datetime
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
    # Part 1: Font import + Base theme, layout, image styles
    st.markdown("""<style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
        @keyframes gradientShift { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
        @keyframes fadeInUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
        @keyframes pulseGlow { 0%,100%{box-shadow:0 0 15px rgba(142,45,226,0.3)} 50%{box-shadow:0 0 30px rgba(142,45,226,0.6)} }
        *,.stApp,.stApp p,.stApp span,.stApp div,.stApp label,.stApp input,.stApp textarea,.stApp button,.stApp h1,.stApp h2,.stApp h3,.stApp h4{font-family:'Poppins',sans-serif!important}
        .stApp{background:linear-gradient(135deg,#0a0a1a 0%,#1a0a2e 25%,#16213e 50%,#0a0a1a 75%,#1a0533 100%);background-size:400% 400%;animation:gradientShift 15s ease infinite;color:#e8e8f0}
        .block-container{padding-bottom:100px!important}
        h1{background:linear-gradient(135deg,#a855f7,#6366f1,#06b6d4)!important;-webkit-background-clip:text!important;-webkit-text-fill-color:transparent!important;font-weight:800!important;letter-spacing:-0.5px!important}
        h2,h3{color:#c4b5fd!important;font-weight:600!important}
        [data-testid="column"] [data-testid="stVerticalBlock"]{gap:0!important}
        [data-testid="column"]{padding:6px!important}
        .img-container{position:relative;width:100%;margin:0}
        .img-container img{aspect-ratio:2/3!important;object-fit:cover!important;width:100%!important;border-radius:16px 16px 0 0!important;display:block;border:1px solid rgba(167,139,250,0.2);transition:transform 0.3s ease,filter 0.3s ease}
        .img-container:hover img{transform:scale(1.02);filter:brightness(1.1)}
        .filename-bar{background:rgba(15,10,35,0.85);backdrop-filter:blur(10px);color:#c4b5fd;text-align:center;font-size:11px;font-weight:500;padding:8px;width:100%;border-left:1px solid rgba(167,139,250,0.15);border-right:1px solid rgba(167,139,250,0.15);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;letter-spacing:0.3px}
        .pilih-btn-wrap{width:100%}
        .pilih-btn-wrap .stButton button{width:100%!important;border-radius:0 0 16px 16px!important;border:none!important;font-weight:600;padding:12px 0!important;font-size:13px!important;letter-spacing:0.5px;transition:all 0.3s cubic-bezier(0.4,0,0.2,1)!important}
        .pilih-btn-wrap .stButton button:hover{transform:translateY(-2px)!important;filter:brightness(1.15)!important}
        .btn-purple button{background:linear-gradient(135deg,#8b5cf6 0%,#6d28d9 50%,#7c3aed 100%)!important;color:#fff!important;box-shadow:0 4px 15px rgba(139,92,246,0.3)!important}
        .btn-blue button{background:linear-gradient(135deg,#06b6d4 0%,#3b82f6 50%,#8b5cf6 100%)!important;color:#fff!important;box-shadow:0 4px 15px rgba(59,130,246,0.3)!important}
    </style>""", unsafe_allow_html=True)
    
    # Part 2: Sticky bar, sidebar, inputs, tabs, login card styles
    st.markdown("""<style>
        .sticky-bottom-bar{position:fixed;bottom:0;left:0;width:100%;background:rgba(10,8,30,0.85);backdrop-filter:blur(20px) saturate(180%);border-top:1px solid rgba(139,92,246,0.4);padding:16px 24px;display:flex;justify-content:space-between;align-items:center;z-index:99999;box-shadow:0 -8px 32px rgba(0,0,0,0.5)}
        .sticky-text{color:#e8e8f0;font-weight:600;font-size:15px;margin:0}
        .sticky-btn{background:linear-gradient(135deg,#06b6d4,#8b5cf6);color:#fff!important;text-decoration:none!important;padding:12px 28px;border-radius:50px;font-weight:600;font-size:14px;box-shadow:0 4px 20px rgba(139,92,246,0.4);transition:all 0.3s cubic-bezier(0.4,0,0.2,1);letter-spacing:0.3px}
        .sticky-btn:hover{filter:brightness(1.15);transform:scale(1.05) translateY(-2px);box-shadow:0 8px 30px rgba(139,92,246,0.5)}
        [data-testid="stSidebar"]{background:rgba(10,8,30,0.95)!important;backdrop-filter:blur(20px);border-right:1px solid rgba(139,92,246,0.3)!important}
        [data-testid="stSidebar"] .stButton button{background:linear-gradient(135deg,#8b5cf6,#6d28d9)!important;color:#fff!important;border:none!important;border-radius:12px!important;font-weight:600!important;transition:all 0.3s ease!important}
        [data-testid="stSidebar"] .stButton button:hover{transform:translateY(-2px)!important;filter:brightness(1.1)!important}
        .stTextInput input,.stTextArea textarea{background:rgba(30,20,60,0.6)!important;border:1px solid rgba(139,92,246,0.3)!important;border-radius:12px!important;color:#e8e8f0!important;transition:border-color 0.3s ease!important}
        .stTextInput input:focus,.stTextArea textarea:focus{border-color:#8b5cf6!important;box-shadow:0 0 15px rgba(139,92,246,0.2)!important}
        .stTabs [data-baseweb="tab-list"]{background:rgba(30,20,60,0.4);border-radius:16px;padding:4px;border:1px solid rgba(139,92,246,0.2)}
        .stTabs [data-baseweb="tab"]{border-radius:12px!important;font-weight:500!important;color:#a5a5c0!important}
        .stTabs [aria-selected="true"]{background:linear-gradient(135deg,#8b5cf6,#6d28d9)!important;color:#fff!important}
        .streamlit-expanderHeader{background:rgba(30,20,60,0.5)!important;border-radius:12px!important;border:1px solid rgba(139,92,246,0.2)!important}
        .login-card{background:rgba(20,15,45,0.7);backdrop-filter:blur(24px) saturate(180%);padding:40px 35px;border-radius:24px;border:1px solid rgba(139,92,246,0.25);box-shadow:0 20px 60px rgba(0,0,0,0.4),0 0 40px rgba(139,92,246,0.1);animation:fadeInUp 0.6s ease-out}
        .login-title{text-align:center;font-size:28px;font-weight:700;background:linear-gradient(135deg,#a855f7,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}
        .login-subtitle{text-align:center;color:#8888aa;font-size:14px;margin-bottom:24px}
        .login-error{background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.4);border-radius:12px;padding:12px 16px;color:#fca5a5;font-size:14px;font-weight:500;text-align:center;margin-top:12px;animation:fadeInUp 0.3s ease-out}
        .stButton button{transition:all 0.3s cubic-bezier(0.4,0,0.2,1)!important}
        ::-webkit-scrollbar{width:6px}
        ::-webkit-scrollbar-track{background:rgba(10,8,30,0.5)}
        ::-webkit-scrollbar-thumb{background:rgba(139,92,246,0.4);border-radius:3px}
        ::-webkit-scrollbar-thumb:hover{background:rgba(139,92,246,0.6)}
    </style>""", unsafe_allow_html=True)
    
    # Part 3: Dashboard, project cards, gallery, mobile responsive
    st.markdown("""<style>
        .stat-card{background:rgba(20,15,45,0.6);backdrop-filter:blur(16px);border:1px solid rgba(139,92,246,0.2);border-radius:16px;padding:20px;text-align:center;transition:all 0.3s ease}
        .stat-card:hover{transform:translateY(-4px);box-shadow:0 8px 25px rgba(139,92,246,0.2);border-color:rgba(139,92,246,0.4)}
        .stat-number{font-size:32px;font-weight:800;background:linear-gradient(135deg,#a855f7,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
        .stat-label{font-size:13px;color:#8888aa;margin-top:4px;font-weight:500}
        .project-card{background:rgba(20,15,45,0.5);backdrop-filter:blur(12px);border:1px solid rgba(139,92,246,0.2);border-radius:16px;padding:20px;margin-bottom:12px;transition:all 0.3s ease;animation:fadeInUp 0.4s ease-out}
        .project-card:hover{border-color:rgba(139,92,246,0.4);box-shadow:0 4px 20px rgba(139,92,246,0.15)}
        .project-name{font-size:16px;font-weight:600;color:#e8e8f0;margin-bottom:4px}
        .project-id{font-size:11px;color:#6b6b8a;word-break:break-all}
        .project-link{font-size:12px;color:#8b5cf6;word-break:break-all}
        .gallery-thumb{border-radius:10px;border:1px solid rgba(139,92,246,0.15);transition:transform 0.3s ease}
        .gallery-thumb:hover{transform:scale(1.05)}
        .welcome-banner{background:linear-gradient(135deg,rgba(139,92,246,0.15),rgba(6,182,212,0.1));border:1px solid rgba(139,92,246,0.2);border-radius:20px;padding:28px 24px;margin-bottom:24px;animation:fadeInUp 0.5s ease-out}
        .welcome-text{font-size:14px;color:#a5a5c0;margin-top:6px}
        .form-card{background:rgba(20,15,45,0.5);backdrop-filter:blur(12px);border:1px solid rgba(139,92,246,0.2);border-radius:16px;padding:24px;margin-top:8px}
        .section-title{font-size:18px;font-weight:600;color:#c4b5fd;margin-bottom:12px}
        .empty-state{text-align:center;padding:40px 20px;color:#6b6b8a}
        .empty-state-icon{font-size:48px;margin-bottom:12px}
        .empty-state-text{font-size:14px}
        .del-btn button{background:linear-gradient(135deg,#ef4444,#dc2626)!important;color:#fff!important;border:none!important;border-radius:10px!important;font-size:12px!important;padding:6px 12px!important}
        .del-btn button:hover{filter:brightness(1.15)!important;transform:scale(1.05)!important}
        .view-btn button{background:linear-gradient(135deg,#8b5cf6,#6d28d9)!important;color:#fff!important;border:none!important;border-radius:10px!important;font-size:12px!important;padding:6px 12px!important}
        .copy-link{background:rgba(139,92,246,0.1);border:1px dashed rgba(139,92,246,0.3);border-radius:10px;padding:8px 12px;font-size:12px;color:#a78bfa;word-break:break-all;margin:8px 0}
        @media(max-width:768px){
            .block-container{padding-left:12px!important;padding-right:12px!important;padding-top:20px!important}
            h1{font-size:22px!important}
            .stat-card{padding:14px}
            .stat-number{font-size:24px}
            .stat-label{font-size:11px}
            .project-card{padding:14px}
            .welcome-banner{padding:18px 14px}
            .sticky-bottom-bar{padding:10px 14px}
            .sticky-text{font-size:13px}
            .sticky-btn{padding:8px 16px;font-size:12px}
            [data-testid="column"]{padding:3px!important}
        }
    </style>""", unsafe_allow_html=True)

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
    elif action == "delete" and name in data:
        del data[name]
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
    if "login_error" not in st.session_state:
        st.session_state["login_error"] = ""
    
    if not st.session_state["logged_in"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <div style="background:rgba(20,15,45,0.7);backdrop-filter:blur(24px) saturate(180%);padding:40px 35px 20px;border-radius:24px;border:1px solid rgba(139,92,246,0.25);box-shadow:0 20px 60px rgba(0,0,0,0.4),0 0 40px rgba(139,92,246,0.1);margin-bottom:20px;">
                    <div style="text-align:center;font-size:28px;font-weight:700;background:linear-gradient(135deg,#a855f7,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px;">🔐 Creative.pick</div>
                    <div style="text-align:center;color:#8888aa;font-size:14px;margin-bottom:10px;">Masuk ke Dashboard Admin</div>
                </div>
            """, unsafe_allow_html=True)
            u = st.text_input("Username", placeholder="Masukkan username")
            p = st.text_input("Password", type="password", placeholder="Masukkan password")
            
            if st.button("🚀 Masuk", use_container_width=True):
                if not u or not p:
                    st.session_state["login_error"] = "⚠️ Username dan Password tidak boleh kosong!"
                    st.rerun()
                elif u == ADMIN_USER and p == ADMIN_PASS:
                    st.session_state["login_error"] = ""
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.session_state["login_error"] = "❌ Username atau Password salah! Silakan coba lagi."
                    st.rerun()
            
            if st.session_state["login_error"]:
                st.markdown(f'<div class="login-error">{st.session_state["login_error"]}</div>', unsafe_allow_html=True)
        return

    st.title("📸 Dashboard Fotografer")
    st.sidebar.button("🚪 Log Out", on_click=lambda: st.session_state.update({"logged_in": False}))
    
    st.sidebar.divider()
    st.sidebar.header("📥 Download Project")
    dl_folder_id = st.sidebar.text_input("ID Folder Project", placeholder="Paste Folder ID GDrive")
    dl_list_names = st.sidebar.text_area("Paste List Nama File dari Client", help="Pisahkan dengan baris baru")
    
    if st.sidebar.button("⚡ Generate Download ZIP"):
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

    # --- Welcome Banner + Stats ---
    projects = manage_db()
    st.markdown(f"""
        <div class="welcome-banner">
            <div style="font-size:20px;font-weight:700;color:#e8e8f0;">👋 Selamat datang, Admin!</div>
            <div class="welcome-text">Kelola semua project fotografi Anda dari sini.</div>
        </div>
    """, unsafe_allow_html=True)

    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{len(projects)}</div><div class="stat-label">📂 Total Project</div></div>', unsafe_allow_html=True)
    with sc2:
        today = datetime.date.today().strftime("%d %b %Y")
        st.markdown(f'<div class="stat-card"><div class="stat-number" style="font-size:20px">{today}</div><div class="stat-label">📅 Hari Ini</div></div>', unsafe_allow_html=True)
    with sc3:
        st.markdown(f'<div class="stat-card"><div class="stat-number">✨</div><div class="stat-label">🚀 Creative.pick</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # --- Tabs ---
    tab1, tab2 = st.tabs(["➕ Buat Project Baru", "📂 Riwayat Project"])
    
    with tab1:
        st.markdown('<div class="section-title">🎯 Buat Link Gallery Baru</div>', unsafe_allow_html=True)
        c_name = st.text_input("Nama Client", placeholder="Contoh: Wisuda Andi")
        g_url = st.text_input("Link Folder Google Drive", placeholder="Paste link folder GDrive di sini")
        if st.button("🚀 Buat Project", use_container_width=True):
            fid = re.search(r'folders/([\w-]+)', g_url)
            fid = fid.group(1) if fid else g_url
            if c_name and fid:
                manage_db("write", c_name, fid)
                st.success("✅ Project berhasil dibuat!")
                link = f"{BASE_URL}/?folder={fid}"
                st.markdown(f'<div class="copy-link">🔗 {link}</div>', unsafe_allow_html=True)
                st.code(link, language=None)
            else:
                st.warning("⚠️ Mohon isi Nama Client dan Link Folder GDrive.")

    with tab2:
        projects = manage_db()
        if not projects:
            st.markdown("""
                <div class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <div class="empty-state-text">Belum ada project. Buat project pertama Anda!</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            for name, fid in list(projects.items()):
                st.markdown(f"""
                    <div class="project-card">
                        <div class="project-name">📁 {name}</div>
                        <div class="project-link">🔗 {BASE_URL}/?folder={fid}</div>
                    </div>
                """, unsafe_allow_html=True)

                # Gallery preview: show thumbnails from GDrive
                try:
                    service = get_gdrive_service()
                    results = service.files().list(
                        q=f"'{fid}' in parents and mimeType contains 'image/' and trashed = false",
                        pageSize=6, fields="files(id, name)").execute()
                    thumbs = results.get('files', [])
                    if thumbs:
                        gcols = st.columns(min(len(thumbs), 3))
                        for ti, thumb in enumerate(thumbs[:6]):
                            with gcols[ti % 3]:
                                img = get_processed_image(thumb['id'])
                                if img:
                                    st.image(img, caption=thumb['name'], use_container_width=True)
                    else:
                        st.caption("📷 Tidak ada preview foto tersedia.")
                except Exception:
                    st.caption("⚠️ Gagal memuat preview foto.")

                # Action buttons
                bc1, bc2, bc3 = st.columns([2, 1, 1])
                with bc1:
                    st.code(f"{BASE_URL}/?folder={fid}", language=None)
                with bc2:
                    st.markdown('<div class="view-btn">', unsafe_allow_html=True)
                    if st.button(f"👁️ Lihat", key=f"v_{fid}"):
                        st.query_params["folder"] = fid
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with bc3:
                    st.markdown('<div class="del-btn">', unsafe_allow_html=True)
                    if st.button(f"🗑️ Hapus", key=f"d_{fid}"):
                        manage_db("delete", name)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("<hr style='border:none;border-top:1px solid rgba(139,92,246,0.15);margin:16px 0'>", unsafe_allow_html=True)

# ==========================================
# 5. RUNNER
# ==========================================
if __name__ == "__main__":
    fid_param = st.query_params.get("folder")
    if fid_param: 
        page_client(fid_param)
    else: 
        page_admin()