import streamlit as st
import json
from io import StringIO
import hashlib

st.set_page_config(layout="wide")

def get_file_hash(content: str) -> str:
    """Генерирует уникальный хеш содержимого файла"""
    return hashlib.md5(content.encode()).hexdigest()

def load_data(file_content):
    """Load data from file content"""
    data = []
    for line in file_content.splitlines():
        line = line.strip()
        if line:
            data.append(json.loads(line))
    return data

def render_dialog(dialog_text):
    """Render dialog with proper formatting"""
    dialog_lines = dialog_text.split('\n')
    dialog_html = '<div class="dialog-container" id="dialog-container">'
    for line in dialog_lines:
        if line.startswith('Клиент:'):
            dialog_html += f'<div class="client-message"><strong>Клиент:</strong></div><div>{line[len("Клиент:"):].strip()}</div><br>'
        elif line.startswith('Менеджер:'):
            dialog_html += f'<div class="manager-message"><strong>Менеджер:</strong></div><div>{line[len("Менеджер:"):].strip()}</div><br>'
        else:
            dialog_html += f'<div>{line}</div><br>'
    dialog_html += '</div>'
    return dialog_html

def save_current_item():
    """Сохраняет текущие значения из виджетов в output_data + показывает уведомление"""
    current_idx = st.session_state.current_index
    client_status_key = f'client_status_{current_idx}'
    success_key = f'success_{current_idx}'
    
    if client_status_key in st.session_state and success_key in st.session_state:
        prev_status = st.session_state.output_data[current_idx].get('client_status')
        prev_success = st.session_state.output_data[current_idx].get('success')
        
        new_status = st.session_state[client_status_key]
        new_success = st.session_state[success_key]
        
        if prev_status != new_status or prev_success != new_success:
            st.session_state.output_data[current_idx]['client_status'] = new_status
            st.session_state.output_data[current_idx]['success'] = new_success
            st.toast("Разметка сохранена!", icon="💾", duration=1)

def main():
    st.title("**Dialogue labeling**")
    
    uploaded_file = st.file_uploader("Загрузите файл JSONL", type=['jsonl'])
    
    if uploaded_file is not None:
        file_content = uploaded_file.getvalue().decode("utf-8")
        file_hash = get_file_hash(file_content)
        
        if ('file_hash' not in st.session_state or 
            st.session_state.file_hash != file_hash):
            
            original_data = load_data(file_content)
            
            st.session_state.output_data = original_data.copy()
            st.session_state.current_index = 0
            st.session_state.file_name = uploaded_file.name
            st.session_state.file_hash = file_hash
            
            for i, item in enumerate(st.session_state.output_data):
                if 'client_status' not in item:
                    st.session_state.output_data[i]['client_status'] = None
                if 'success' not in item:
                    st.session_state.output_data[i]['success'] = None
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("ИНСТРУКЦИЯ ПО РАЗМЕТКЕ")
            st.markdown("""
            **client_status:**
            - **new** - новый клиент, который впервые обращается
            - **current** - действующий клиент, который уже обслуживался ранее
            
            **success:**
            - **1** - разговор завершился успешно
            - **0** - разговор не завершился успешно
            
            **ШАГИ:**
            1. Прочитайте диалог внимательно
            2. Оцените статус клиента
            3. Оцените успешность разговора согласно **критериям**
            4. Отметьте соответствующие значения в меню
            5. Используйте кнопки навигации для перехода
            
            **КРИТЕРИИ УСПЕШНОСТИ:**
            Для нового клиента:
            - Подписание договора
            - Оплата обучения
            
            Для действующего клиента:
            - (Критерии в разработке)
            """)
            
            st.write(f"**Прогресс:** {st.session_state.current_index + 1} / {len(st.session_state.output_data)}")
            
            if st.button("Начать сначала (изменения не сохранятся)", use_container_width=True):
                original_data = load_data(file_content)
                st.session_state.output_data = original_data.copy()
                st.session_state.current_index = 0
                
                for i, item in enumerate(st.session_state.output_data):
                    if 'client_status' not in item:
                        st.session_state.output_data[i]['client_status'] = None
                    if 'success' not in item:
                        st.session_state.output_data[i]['success'] = None
                
                st.rerun()
            
            save_current_item()
            
            output_filename = f"labeled_{uploaded_file.name}"
            output_data_str = ""
            for item in st.session_state.output_data:
                output_data_str += json.dumps(item, ensure_ascii=False) + '\n'
            
            st.download_button(
                label="Скачать файл с разметкой",
                data=output_data_str,
                file_name=output_filename,
                mime="application/jsonl",
                use_container_width=True
            )
        
        with col2:
            current_item = st.session_state.output_data[st.session_state.current_index]
            
            st.subheader(f"Диалог #{current_item['id']}")
            
            st.markdown("""
            <style>
            .dialog-container {
                height: 600px;
                overflow-y: auto;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
                margin-bottom: 20px;
                font-size: 16px;
            }
            .client-message {
                color: #1f77b4;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .manager-message {
                color: #ff7f0e;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .dialog-container::-webkit-scrollbar {
                width: 8px;
            }
            .dialog-container::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 4px;
            }
            .dialog-container::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 4px;
            }
            .dialog-container::-webkit-scrollbar-thumb:hover {
                background: #555;
            }
            </style>
            <script>
            function resetScroll() {
                const dialogContainer = document.getElementById('dialog-container');
                if (dialogContainer) {
                    dialogContainer.scrollTop = 0;
                }
            }
            resetScroll();
            setTimeout(resetScroll, 300);
            </script>
            """, unsafe_allow_html=True)
            
            dialog_html = render_dialog(current_item['text'])
            st.markdown(dialog_html, unsafe_allow_html=True)
            
            client_status_options = ["new", "current"]
            success_options = [0, 1]
            
            current_client_status = current_item.get('client_status', None)
            current_success = current_item.get('success', None)
            
            client_status_index = 0
            if current_client_status in client_status_options:
                client_status_index = client_status_options.index(current_client_status)
            
            success_index = 0
            if current_success in success_options:
                success_index = success_options.index(current_success)
            
            client_status = st.selectbox(
                "Статус клиента",
                options=client_status_options,
                index=client_status_index,
                key=f'client_status_{st.session_state.current_index}',
                on_change=save_current_item
            )
            
            success = st.selectbox(
                "Успех",
                options=success_options,
                index=success_index,
                key=f'success_{st.session_state.current_index}',
                on_change=save_current_item
            )
            
            nav_col1, nav_col2 = st.columns(2)
            
            with nav_col1:
                if st.button("← Предыдущий", use_container_width=True, disabled=st.session_state.current_index == 0):
                    save_current_item() 
                    st.session_state.current_index -= 1
                    st.rerun()
            
            with nav_col2:
                if st.button("Следующий →", use_container_width=True, disabled=st.session_state.current_index >= len(st.session_state.output_data) - 1):
                    save_current_item()
                    st.session_state.current_index += 1
                    st.rerun()

if __name__ == "__main__":
    main()