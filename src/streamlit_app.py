"""
Streamlit dashboard for File Watch.
"""

import sys
from pathlib import Path

# Ensure project root is on path when running via streamlit run
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import httpx

from src.logger import logger

st.set_page_config(page_title="File Watch", page_icon="📦", layout="wide")

API_BASE = st.sidebar.text_input("API URL", value="http://127.0.0.1:8000", key="api_base")
API_PREFIX = f"{API_BASE.rstrip('/')}/api/v1/storage"

st.title("File Watch")
st.markdown("Dashboard for file management and backup.")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "Health",
    "Single File CRUD",
    "List Files",
    "Bulk Operations",
])


def api_get(path: str, params: dict | None = None):
    with httpx.Client(timeout=10.0) as client:
        r = client.get(f"{API_PREFIX}{path}", params=params)
        r.raise_for_status()
        return r.json()


def api_post(path: str, json: dict):
    with httpx.Client(timeout=10.0) as client:
        r = client.post(f"{API_PREFIX}{path}", json=json)
        r.raise_for_status()
        return r.json()


def api_put(path: str, json: dict):
    with httpx.Client(timeout=10.0) as client:
        r = client.put(f"{API_PREFIX}{path}", json=json)
        r.raise_for_status()
        return r.json()


def api_delete(path: str, json: dict | None = None):
    with httpx.Client(timeout=10.0) as client:
        r = client.request("DELETE", f"{API_PREFIX}{path}", json=json)
        r.raise_for_status()
        return r.json()


# --- Health ---
with tab1:
    st.subheader("Storage Health")
    if st.button("Check Health", key="health_btn"):
        try:
            data = api_get("/health")
            if data.get("status") == "ok":
                st.success("Database connected")
            else:
                st.error(data.get("detail", "Unknown error"))
        except httpx.ConnectError:
            st.error("Cannot connect to API. Is the server running at {}?".format(API_BASE))
        except Exception as e:
            st.exception(e)
    st.markdown("---")
    st.markdown("[API Docs]({}/docs) | [API Root]({})".format(API_BASE, API_BASE))


# --- Single File CRUD ---
with tab2:
    st.subheader("Single File CRUD")
    crud_op = st.radio("Operation", ["Create", "Get", "Update", "Delete"], horizontal=True, key="crud_op")

    if crud_op == "Create":
        with st.form("create_form"):
            file_name = st.text_input("File name")
            size = st.number_input("Size (bytes)", min_value=0, value=0)
            hash_val = st.text_input("Hash")
            complete_path = st.text_input("Complete path")
            file_created_at = st.text_input("File created at (ISO datetime, optional)", placeholder="2024-01-15T10:30:00")
            file_modified_at = st.text_input("File modified at (ISO datetime, optional)", placeholder="2024-01-15T12:00:00")
            if st.form_submit_button("Create"):
                try:
                    payload = {
                        "file_name": file_name,
                        "size": size,
                        "hash": hash_val,
                        "complete_path": complete_path,
                    }
                    if file_created_at:
                        payload["file_created_at"] = file_created_at
                    if file_modified_at:
                        payload["file_modified_at"] = file_modified_at
                    data = api_post("/files", payload)
                    st.success("Created")
                    st.json(data)
                except httpx.HTTPStatusError as e:
                    st.error(e.response.text)
                except Exception as e:
                    st.exception(e)

    elif crud_op == "Get":
        file_id = st.number_input("File ID", min_value=1, value=1, key="get_id")
        if st.button("Get", key="get_btn"):
            try:
                data = api_get(f"/files/{file_id}")
                st.json(data)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    st.error("Not found")
                else:
                    st.error(e.response.text)
            except Exception as e:
                st.exception(e)

    elif crud_op == "Update":
        with st.form("update_form"):
            file_id = st.number_input("File ID", min_value=1, value=1, key="upd_id")
            file_name = st.text_input("File name (leave empty to keep)")
            size = st.number_input("Size (bytes, -1 to keep)", min_value=-1, value=-1)
            hash_val = st.text_input("Hash (leave empty to keep)")
            complete_path = st.text_input("Complete path (leave empty to keep)")
            file_created_at = st.text_input("File created at (leave empty to keep)", key="upd_created")
            file_modified_at = st.text_input("File modified at (leave empty to keep)", key="upd_modified")
            if st.form_submit_button("Update"):
                body = {}
                if file_name:
                    body["file_name"] = file_name
                if size >= 0:
                    body["size"] = size
                if hash_val:
                    body["hash"] = hash_val
                if complete_path:
                    body["complete_path"] = complete_path
                if file_created_at:
                    body["file_created_at"] = file_created_at
                if file_modified_at:
                    body["file_modified_at"] = file_modified_at
                if not body:
                    st.warning("No fields to update")
                else:
                    try:
                        data = api_put(f"/files/{file_id}", body)
                        st.success("Updated")
                        st.json(data)
                    except httpx.HTTPStatusError as e:
                        st.error(e.response.text)
                    except Exception as e:
                        st.exception(e)

    elif crud_op == "Delete":
        file_id = st.number_input("File ID", min_value=1, value=1, key="del_id")
        if st.button("Delete", key="del_btn", type="primary"):
            try:
                data = api_delete(f"/files/{file_id}")
                st.success("Deleted")
                st.json(data)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    st.error("Not found")
                else:
                    st.error(e.response.text)
            except Exception as e:
                st.exception(e)


# --- List Files ---
with tab3:
    st.subheader("List File Records")
    path_filter = st.text_input("Filter by path (substring)", key="path_filter")
    col1, col2 = st.columns(2)
    with col1:
        limit = st.number_input("Limit", min_value=1, max_value=1000, value=100)
    with col2:
        offset = st.number_input("Offset", min_value=0, value=0)
    if st.button("List", key="list_btn"):
        try:
            params = {"limit": limit, "offset": offset}
            if path_filter:
                params["path"] = path_filter
            data = api_get("/files", params)
            st.metric("Records", len(data))
            if data:
                st.dataframe(data, use_container_width=True)
            else:
                st.info("No records")
        except Exception as e:
            st.exception(e)


# --- Bulk Operations ---
with tab4:
    st.subheader("Bulk Operations")
    bulk_op = st.radio("Operation", ["Bulk Create", "Bulk Get", "Bulk Delete"], horizontal=True, key="bulk_op")

    if bulk_op == "Bulk Create":
        st.markdown("Enter JSON array of file records:")
        st.code('{"files": [{"file_name": "a.txt", "size": 100, "hash": "abc", "complete_path": "/path/a.txt", "file_created_at": "2024-01-15T10:30:00", "file_modified_at": "2024-01-15T12:00:00"}]}')
        bulk_json = st.text_area("JSON", height=150, key="bulk_create_json")
        if st.button("Bulk Create", key="bulk_create_btn"):
            try:
                import json
                body = json.loads(bulk_json)
                data = api_post("/files/bulk", body)
                st.success(f"Created {data.get('created', 0)} records")
                st.json(data)
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
            except httpx.HTTPStatusError as e:
                st.error(e.response.text)
            except Exception as e:
                st.exception(e)

    elif bulk_op == "Bulk Get":
        ids_str = st.text_input("Comma-separated IDs", placeholder="1, 2, 3", key="bulk_get_ids")
        if st.button("Bulk Get", key="bulk_get_btn"):
            try:
                ids = [int(x.strip()) for x in ids_str.split(",") if x.strip()]
                if not ids:
                    st.warning("Enter at least one ID")
                else:
                    data = api_post("/files/bulk/get", {"ids": ids})
                    st.metric("Records", len(data))
                    if data:
                        st.dataframe(data, use_container_width=True)
                    else:
                        st.info("No records found")
            except ValueError:
                st.error("IDs must be integers")
            except Exception as e:
                st.exception(e)

    elif bulk_op == "Bulk Delete":
        ids_str = st.text_input("Comma-separated IDs to delete", placeholder="1, 2, 3", key="bulk_del_ids")
        if st.button("Bulk Delete", key="bulk_del_btn", type="primary"):
            try:
                ids = [int(x.strip()) for x in ids_str.split(",") if x.strip()]
                if not ids:
                    st.warning("Enter at least one ID")
                else:
                    data = api_delete("/files/bulk", {"ids": ids})
                    st.success(f"Deleted {data.get('deleted', 0)} records")
                    st.json(data)
            except ValueError:
                st.error("IDs must be integers")
            except Exception as e:
                st.exception(e)
