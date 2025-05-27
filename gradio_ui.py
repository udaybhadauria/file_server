import gradio as gr
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("SERVER_URL", "http://127.0.0.1:8369")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Store token in memory
jwt_token = None

def login(username, password):
    global jwt_token
    try:
        response = requests.post(f"{API_BASE}/login", json={"username": username, "password": password})
        if response.status_code == 200:
            jwt_token = response.json()['token']
            return "✅ Login successful!", gr.update(visible=True), gr.update(visible=True)
        else:
            return "❌ Login failed! Check credentials.", gr.update(visible=False), gr.update(visible=False)
    except Exception as e:
        return f"⚠️ Error: {e}", gr.update(visible=False), gr.update(visible=False)

def upload_file(file):
    if not jwt_token:
        return "❌ Please login first."
    try:
        with open(file.name, "rb") as f:
            response = requests.post(
                f"{API_BASE}/upload",
                files={"file": f},
                headers={"Authorization": f"Bearer {jwt_token}"}
            )
        return response.json().get("message", "❌ Upload failed")
    except Exception as e:
        return f"⚠️ Error: {e}"

def list_files():
    if not jwt_token:
        return [], "❌ Please login first."
    try:
        response = requests.get(f"{API_BASE}/list", headers={"Authorization": f"Bearer {jwt_token}"})
        if response.status_code == 200:
            files = response.json()['files']
            table = [[f['name'], f['size_kb'], f['modified']] for f in files]
            return table, "✅ Files listed below:"
        return [], response.json().get("message", "❌ Failed to fetch file list")
    except Exception as e:
        return [], f"⚠️ Error: {e}"

def delete_file(filename):
    if not jwt_token:
        return "❌ Please login first."
    try:
        response = requests.delete(
            f"{API_BASE}/delete/{filename}",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        return response.json().get("message", "❌ Delete failed")
    except Exception as e:
        return f"⚠️ Error: {e}"

def download_link(filename):
    return f"{API_BASE}/public_download/{filename}"

# Gradio Interface
with gr.Blocks(title="📁 Raspberry Pi File Server UI") as demo:
    gr.Markdown("# 🔐 Login to File Server")

    with gr.Row():
        username_input = gr.Textbox(label="Username", value=ADMIN_USERNAME or "")
        password_input = gr.Textbox(label="Password", type="password", value=ADMIN_PASSWORD or "")

    login_btn = gr.Button("Login")
    login_status = gr.Textbox(label="Login Status", interactive=False)

    gr.Markdown("## 📤 Upload File")
    with gr.Column(visible=False) as upload_section:
        upload_file_input = gr.File(label="Select File")
        upload_btn = gr.Button("Upload")
        upload_status = gr.Textbox(label="Upload Status", interactive=False)

    gr.Markdown("## 📄 File List")
    with gr.Column(visible=False) as file_section:
        list_btn = gr.Button("Refresh File List")
        file_table = gr.Dataframe(headers=["Name", "Size (KB)", "Modified"], interactive=False)
        file_status = gr.Textbox(label="List Status", interactive=False)

        gr.Markdown("### 🗑️ Delete or 🔗 Download a File")
        delete_input = gr.Textbox(label="Enter Filename to Delete")
        delete_btn = gr.Button("Delete File")
        delete_status = gr.Textbox(label="Delete Status", interactive=False)

        download_input = gr.Textbox(label="Enter Filename to Get Download Link")
        download_link_output = gr.Textbox(label="Download URL", interactive=False)

    # Bind event callbacks
    login_btn.click(fn=login, inputs=[username_input, password_input], outputs=[login_status, upload_section, file_section])
    upload_btn.click(fn=upload_file, inputs=[upload_file_input], outputs=[upload_status])
    list_btn.click(fn=list_files, outputs=[file_table, file_status])
    delete_btn.click(fn=delete_file, inputs=[delete_input], outputs=[delete_status])
    download_input.change(fn=download_link, inputs=[download_input], outputs=[download_link_output])

# Launch UI
demo.launch(server_name="0.0.0.0", server_port=7860)
