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

# Camera: auto-add captured photo to session and clear the preview so camera stays ready
with col1:
    st.write("Use your device camera")
    cam = st.camera_input("Take a photo")
    if cam is not None:
        cam_bytes = cam.getvalue()
        # avoid duplicate adds by comparing last_camera
        if st.session_state.get("last_camera") != cam_bytes:
            from datetime import datetime as _dt
            st.session_state.photos.append({
                "bytes": cam_bytes,
                "filename": f"camera_{len(st.session_state.photos)+1}.jpg",
                "timestamp": _dt.now().strftime("%Y-%m-%d %H:%M:%S"),
                "comment": "",
            })
            st.session_state.last_camera = cam_bytes
            # re-run to clear the camera input immediately
            st.experimental_rerun()

with col2:
    st.write("Or upload from gallery")
    uploaded = st.file_uploader("Upload images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    if uploaded:
        from datetime import datetime as _dt
    for u in uploaded:
        st.session_state.photos.append({"bytes": u.read(), "filename": u.name, "timestamp": _dt.now().strftime("%Y-%m-%d %H:%M:%S"), "comment": ""})
        st.success(f"Added {len(uploaded)} image(s) to session")

st.markdown("---")

st.header("Session photos")
if len(st.session_state.photos) == 0:
    st.info("No photos yet. Use the camera or upload to start a session.")
else:
    st.write(f"{len(st.session_state.photos)} photo(s) in this session")

    # If reorder info is present in the query params, apply it (coming from the JS Sortable UI)
    params = st.experimental_get_query_params()
    if "order" in params:
        try:
            order_str = params.get("order")[0]
            order = [int(x) for x in order_str.split(",") if x.strip()!='']
            if len(order) == len(st.session_state.photos):
                new_photos = [st.session_state.photos[i] for i in order]
                st.session_state.photos = new_photos
        except Exception:
            st.warning("Could not apply order from UI; ignoring.")
        # clear query params so reloading doesn't reapply
        st.experimental_set_query_params()
        st.experimental_rerun()

        # Render a draggable reorder UI using SortableJS via an HTML component.
        # This posts the new order back by reloading the page with ?order=index,...
        try:
            # prepare HTML list of images as base64
            items_html = []
            for i, p in enumerate(st.session_state.photos):
                b64 = base64.b64encode(p["bytes"]).decode('utf-8')
                items_html.append('<div class="item" data-idx="%d"><img src="data:image/jpeg;base64,%s" style="width:120px; height:auto; display:block;"/><div style="text-align:center;">%d. %s</div></div>' % (i, b64, i+1, p["filename"]))

            items_joined = ''.join(items_html)
            sortable_html = """
<style>
.sortable-wrap { display:flex; gap:8px; flex-wrap:wrap; align-items:flex-start; }
.item { border:1px solid #ddd; padding:6px; background:#fff; border-radius:6px; cursor:grab; }
</style>
<div>
    <div id="sortable" class="sortable-wrap">
        {ITEMS}
    </div>
    <div style="margin-top:8px;">
        <button id="apply">Apply order</button>
        <small style="margin-left:8px;color:#666;">Drag images then click Apply order to commit ordering.</small>
    </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
<script>
    const el = document.getElementById('sortable');
    const sortable = Sortable.create(el, {animation:150});
    document.getElementById('apply').onclick = () => {
        const children = Array.from(el.children);
        const order = children.map(c => c.getAttribute('data-idx'));
        const qs = '?order=' + order.join(',');
        window.location.search = qs;
    };
</script>
""".replace('{ITEMS}', items_joined)
            st.components.v1.html(sortable_html, height=240)
        except Exception:
            st.info("Drag-and-drop reorder UI unavailable — falling back to buttons below.")

        st.markdown("---")

        # Editable labels + controls fallback (Up/Down/Delete) — works regardless of JS
        for idx, p in enumerate(st.session_state.photos):
            cols = st.columns([1, 3, 1, 1, 1])
            with cols[0]:
                st.image(p["bytes"], width=90)
            with cols[1]:
                label = f"Photo {idx+1} - {p.get('timestamp','') }"
                st.write(f"**{label} — {p['filename']}**")
                # editable position input
                new_pos = st.number_input("Position", min_value=1, max_value=len(st.session_state.photos), value=idx+1, key=f"pos_{idx}")
                if st.button("Move", key=f"move_{idx}"):
                    # move item to new_pos (1-based)
                    try:
                        new_index = int(new_pos) - 1
                        if 0 <= new_index < len(st.session_state.photos) and new_index != idx:
                            item = st.session_state.photos.pop(idx)
                            st.session_state.photos.insert(new_index, item)
                            st.experimental_rerun()
                    except Exception:
                        st.warning("Invalid position")
                # Per-photo comment (editable)
                try:
                    comment_val = st.text_area("Comment (optional)", value=p.get('comment',''), key=f"comment_{idx}")
                    # persist back into the photo dict
                    st.session_state.photos[idx]['comment'] = comment_val
                except Exception:
                    # fallback to a single-line input if textarea isn't suitable
                    comment_val = st.text_input("Comment (optional)", value=p.get('comment',''), key=f"comment_fallback_{idx}")
                    st.session_state.photos[idx]['comment'] = comment_val
                # Small per-photo dictation helper (copy/paste style)
                dictation_block = ('''
<div>
  <button id="start_{IDX}">Start</button>
  <button id="stop_{IDX}">Stop</button>
  <button id="copy_{IDX}">Copy</button>
  <div id="result_{IDX}" style="white-space:pre-wrap; border:1px solid #ddd; padding:6px; margin-top:6px; min-height:40px;"></div>
  <script>
    const result_{IDX} = document.getElementById('result_{IDX}');
    let recognition_{IDX} = null;
    if ('webkitSpeechRecognition' in window) {
      recognition_{IDX} = new webkitSpeechRecognition();
      recognition_{IDX}.continuous = true;
      recognition_{IDX}.interimResults = true;
      recognition_{IDX}.onresult = (event) => {
        let interim = '';
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) final += event.results[i][0].transcript;
          else interim += event.results[i][0].transcript;
        }
        result_{IDX}.textContent = final + '\n' + interim;
      };
    } else if ('SpeechRecognition' in window) {
      recognition_{IDX} = new SpeechRecognition();
      recognition_{IDX}.continuous = true;
      recognition_{IDX}.interimResults = true;
      recognition_{IDX}.onresult = (event) => {
        let interim = '';
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) final += event.results[i][0].transcript;
          else interim += event.results[i][0].transcript;
        }
        result_{IDX}.textContent = final + '\n' + interim;
      };
    } else {
      result_{IDX}.textContent = 'Speech recognition not supported in this browser.';
    }
    document.getElementById('start_{IDX}').onclick = () => { if (recognition_{IDX}) recognition_{IDX}.start(); };
    document.getElementById('stop_{IDX}').onclick = () => { if (recognition_{IDX}) recognition_{IDX}.stop(); };
    document.getElementById('copy_{IDX}').onclick = () => { navigator.clipboard.writeText(result_{IDX}.textContent); alert('Copied to clipboard — paste into the comment box.'); };
  </script>
</div>
''').replace('{IDX}', str(idx))
                try:
                    st.components.v1.html(dictation_block, height=120)
                except Exception:
                    pass
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
            photo_comments = {i: p.get('comment', '') for i, p in enumerate(st.session_state.photos)}
            pdf_bytes = generate_multipage_proof_pdf(st.session_state.photos, st.session_state.statement, photo_comments=photo_comments)
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
