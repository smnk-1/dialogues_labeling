import streamlit as st
import json
from io import StringIO
import hashlib  # Для надежного сравнения файлов

# Установим широкий макет страницы
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
    """Сохраняет текущие значения из виджетов в output_data"""
    current_idx = st.session_state.current_index
    client_status_key = f'client_status_{current_idx}'
    success_key = f'success_{current_idx}'
    
    # Сохраняем только если виджеты уже отрендерены
    if client_status_key in st.session_state and success_key in st.session_state:
        st.session_state.output_data[current_idx]['client_status'] = st.session_state[client_status_key]
        st.session_state.output_data[current_idx]['success'] = st.session_state[success_key]

def main():
    st.title("**Dialogue labeling**")
    
    # File upload
    uploaded_file = st.file_uploader("Загрузите файл JSONL", type=['jsonl'])
    
    if uploaded_file is not None:
        # Read the uploaded file content
        file_content = uploaded_file.getvalue().decode("utf-8")
        file_hash = get_file_hash(file_content)
        
        # Initialize or update session state when a new file is uploaded
        if ('file_hash' not in st.session_state or 
            st.session_state.file_hash != file_hash):
            
            # Load original data
            original_data = load_data(file_content)
            
            # Initialize session state with a copy of the data
            st.session_state.output_data = original_data.copy()
            st.session_state.current_index = 0
            st.session_state.file_name = uploaded_file.name
            st.session_state.file_hash = file_hash  # Сохраняем хеш для сравнения
            
            # ВАЖНО: Инициализируем поля ТОЛЬКО если они отсутствуют
            for i, item in enumerate(st.session_state.output_data):
                if 'client_status' not in item:
                    st.session_state.output_data[i]['client_status'] = None
                if 'success' not in item:
                    st.session_state.output_data[i]['success'] = None
        
        # Create two columns with wider layout
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("ИНСТРУКРЦИЯ ПО РАЗМЕТКЕ")
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
            3. Оцените успешность разговора согласно **криетриям**
            4. Отметьте соответствующие значения в меню
            5. Нажмите "Продолжить"
            6. По завершении разметки скачайте файл
                        
            **КРИТЕРИИ УСПЕШНОСТИ ДЛЯ НОВОГО КЛИЕНТА:**
            1. Подписание договора 
            2. Оплата обучения   
            
            **КРИТЕРИИ УСПЕШНОСТИ ДЛЯ ДЕЙСТВУЮЩЕГО КЛИЕНТА:**
            1. (Критерии в разработке)
            """)
            
            # Show current progress in the left column
            st.write(f"**Прогресс:** {st.session_state.current_index + 1} / {len(st.session_state.output_data)}")
            
            # Add reset button at the bottom of the left column
            if st.button("Начать сначала (изменения не сохранятся)", use_container_width=True):
                # Перезагружаем данные из исходного содержимого
                original_data = load_data(file_content)
                st.session_state.output_data = original_data.copy()
                st.session_state.current_index = 0
                
                # Инициализируем поля ТОЛЬКО если отсутствуют
                for i, item in enumerate(st.session_state.output_data):
                    if 'client_status' not in item:
                        st.session_state.output_data[i]['client_status'] = None
                    if 'success' not in item:
                        st.session_state.output_data[i]['success'] = None
                
                st.rerun()
            
            # Перед скачиванием ВСЕГДА сохраняем текущие изменения
            save_current_item()  # Критически важно!
            
            # Download button for current state
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
            # Get current item
            current_item = st.session_state.output_data[st.session_state.current_index]
            
            # Display current dialog in a scrollable container
            st.subheader(f"Диалог #{current_item['id']}")
            
            # Create a scrollable area for the dialog with custom styling
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
            // Reset scroll when page loads
            resetScroll();
            // Also reset scroll after Streamlit updates
            setTimeout(resetScroll, 300);
            </script>
            """, unsafe_allow_html=True)
            
            # Render dialog
            dialog_html = render_dialog(current_item['text'])
            st.markdown(dialog_html, unsafe_allow_html=True)
            
            # Создаем виджеты с автоматическим сохранением при изменении
            client_status_options = ["new", "current"]
            success_options = [0, 1]
            
            # Получаем текущие значения с учетом возможных изменений
            current_client_status = current_item.get('client_status', None)
            current_success = current_item.get('success', None)
            
            client_status_index = 0
            if current_client_status in client_status_options:
                client_status_index = client_status_options.index(current_client_status)
            
            success_index = 0
            if current_success in success_options:
                success_index = success_options.index(current_success)
            
            # Селектбоксы с автоматическим сохранением через on_change
            client_status = st.selectbox(
                "Статус клиента",
                options=client_status_options,
                index=client_status_index,
                key=f'client_status_{st.session_state.current_index}',
                on_change=save_current_item  # Автоматическое сохранение!
            )
            
            success = st.selectbox(
                "Успех",
                options=success_options,
                index=success_index,
                key=f'success_{st.session_state.current_index}',
                on_change=save_current_item  # Автоматическое сохранение!
            )
            
            # Форма теперь только для навигации
            with st.form(key=f'nav_form_{st.session_state.current_index}'):
                submit_button = st.form_submit_button(label='Продолжить', use_container_width=True)
            
            if submit_button:
                # Переход вперед (сохранение уже выполнено через on_change)
                if st.session_state.current_index < len(st.session_state.output_data) - 1:
                    st.session_state.current_index += 1
                    st.rerun()
                else:
                    st.success("Все диалоги размечены!")
            
            # Navigation buttons с сохранением перед переходом
            nav_col1, nav_col2 = st.columns(2)
            
            with nav_col1:
                if st.button("Предыдущий", use_container_width=True, disabled=st.session_state.current_index == 0):
                    save_current_item()  # Критически важно!
                    st.session_state.current_index -= 1
                    st.rerun()
            
            with nav_col2:
                if st.button("Следующий", use_container_width=True, disabled=st.session_state.current_index >= len(st.session_state.output_data) - 1):
                    save_current_item()  # Критически важно!
                    st.session_state.current_index += 1
                    st.rerun()

if __name__ == "__main__":
    main()