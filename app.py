import streamlit as st
from datetime import datetime
import io
import os
import base64

from utils import generate_proof_pdf, generate_multipage_proof_pdf

st.set_page_config(page_title="SnapProof", page_icon="📸")
st.title("📸 SnapProof – Mobile Session Proof Generator")

# Initialize session state
if "photos" not in st.session_state:
    st.session_state.photos = []  # list of dicts {bytes, filename}
if "statement" not in st.session_state:
    st.session_state.statement = ""


st.header("Capture or upload photos")
col1, col2 = st.columns([1, 1])

with col1:
    st.write("Use your device camera")
    cam = st.camera_input("Take a photo")
    # When a camera capture appears, hold it in a pending slot so user can Retake or Continue
    if cam is not None:
        st.session_state.pending_camera = cam.getvalue()
    if "pending_camera" in st.session_state and st.session_state.pending_camera is not None:
        st.image(st.session_state.pending_camera, caption="Preview", use_column_width=True)
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Retake", key="retake_cam"):
                st.session_state.pending_camera = None
                st.experimental_rerun()
        with c2:
            if st.button("Continue", key="cont_cam"):
                from datetime import datetime as _dt
                st.session_state.photos.append({
                    "bytes": st.session_state.pending_camera,
                    "filename": f"camera_{len(st.session_state.photos)+1}.jpg",
                    "timestamp": _dt.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                st.session_state.pending_camera = None
                st.success("Photo added to session")

with col2:
    st.write("Or upload from gallery")
    uploaded = st.file_uploader("Upload images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    if uploaded:
        from datetime import datetime as _dt
        for u in uploaded:
            st.session_state.photos.append({"bytes": u.read(), "filename": u.name, "timestamp": _dt.now().strftime("%Y-%m-%d %H:%M:%S")})
        st.success(f"Added {len(uploaded)} image(s) to session")

st.markdown("---")

st.header("Session photos")
if len(st.session_state.photos) == 0:
    st.info("No photos yet. Use the camera or upload to start a session.")
else:
    st.write(f"{len(st.session_state.photos)} photo(s) in this session")
    for idx, p in enumerate(st.session_state.photos):
        cols = st.columns([1, 4, 1, 1, 1])
        with cols[0]:
            st.image(p["bytes"], width=80)
        with cols[1]:
            # show numbered label
            label = f"Photo {idx+1} - {p.get('timestamp','') }"
            st.write(f"**{label} — {p['filename']}**")
        with cols[2]:
            if st.button("Up", key=f"up_{idx}"):
                if idx > 0:
                    st.session_state.photos[idx-1], st.session_state.photos[idx] = st.session_state.photos[idx], st.session_state.photos[idx-1]
                    st.experimental_rerun()
        with cols[3]:
            if st.button("Down", key=f"down_{idx}"):
                if idx < len(st.session_state.photos)-1:
                    st.session_state.photos[idx+1], st.session_state.photos[idx] = st.session_state.photos[idx], st.session_state.photos[idx+1]
                    st.experimental_rerun()
        with cols[4]:
            if st.button("Delete", key=f"del_{idx}"):
                st.session_state.photos.pop(idx)
                st.experimental_rerun()

    if st.button("View full photos"):
        for p in st.session_state.photos:
            st.image(p["bytes"], use_column_width=True)

st.markdown("---")

st.header("Statement")
st.session_state.statement = st.text_area("Add a statement describing the photos or task", value=st.session_state.statement, height=150)

# Dictation helper (experimental) — uses Web Speech API in the browser; copy/paste into the statement box
st.markdown("**Dictation (experimental):** Click Start/Stop and then click Copy to paste into the statement box.")
dictation_html = '''
<div>
  <button id="start">Start</button>
  <button id="stop">Stop</button>
  <button id="copy">Copy</button>
  <div id="result" style="white-space:pre-wrap; border:1px solid #ddd; padding:10px; margin-top:10px; min-height:50px;"></div>
  <script>
    const result = document.getElementById('result');
    let recognition = null;
    if ('webkitSpeechRecognition' in window) {
      recognition = new webkitSpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.onresult = (event) => {
        let interim = '';
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) final += event.results[i][0].transcript;
          else interim += event.results[i][0].transcript;
        }
        result.textContent = final + '\n' + interim;
      };
    } else if ('SpeechRecognition' in window) {
      recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.onresult = (event) => {
        let interim = '';
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) final += event.results[i][0].transcript;
          else interim += event.results[i][0].transcript;
        }
        result.textContent = final + '\n' + interim;
      };
    } else {
      result.textContent = 'Speech recognition not supported in this browser.';
    }
    document.getElementById('start').onclick = () => { if (recognition) recognition.start(); };
    document.getElementById('stop').onclick = () => { if (recognition) recognition.stop(); };
    document.getElementById('copy').onclick = () => { navigator.clipboard.writeText(result.textContent); alert('Copied to clipboard — paste into the statement box.'); };
  </script>
</div>
'''
st.components.v1.html(dictation_html, height=180)

st.markdown("---")

col_a, col_b = st.columns([1, 1])
with col_a:
    if st.button("✓ Confirm & Generate Proof"):
        if len(st.session_state.photos) == 0:
            st.warning("Add at least one photo before generating the proof.")
        elif not st.session_state.statement.strip():
            st.warning("Please add a statement before generating the proof.")
        else:
            pdf_bytes = generate_multipage_proof_pdf(st.session_state.photos, st.session_state.statement)
            st.success("Proof package generated — download below")
            st.download_button("📄 Download Proof PDF", data=pdf_bytes, file_name="proof.pdf", mime="application/pdf")
            try:
                pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" height="800px" type="application/pdf"></iframe>'
                if st.checkbox("Preview PDF in app"):
                    st.markdown(pdf_display, unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"PDF preview not available: {e}")
with col_b:
    if st.button("Reset session"):
        st.session_state.photos = []
        st.session_state.statement = ""
        st.experimental_rerun()
