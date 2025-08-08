import os
import subprocess
from datetime import datetime

def get_last_modification_date():
    """
    Получает дату последнего изменения кодовой базы.
    Сначала пытается получить дату последнего коммита Git,
    если Git недоступен - использует дату изменения файлов.
    """
    try:
        # Попытка получить дату последнего коммита Git
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cd', '--date=format:%Y-%m-%d %H:%M'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    # Если Git недоступен, используем дату изменения файлов
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        latest_time = 0
        
        # Проверяем основные файлы проекта
        for root, dirs, files in os.walk(script_dir):
            # Пропускаем служебные директории
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'build', 'dist']]
            
            for file in files:
                if file.endswith(('.py', '.json', '.md', '.txt', '.cmd')):
                    file_path = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(file_path)
                        latest_time = max(latest_time, mtime)
                    except OSError:
                        continue
        
        if latest_time > 0:
            return datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M')
    except Exception:
        pass
    
    # Если все остальное не сработало, возвращаем текущую дату
    return datetime.now().strftime('%Y-%m-%d %H:%M')

def get_version_string():
    """
    Возвращает строку версии с датой последнего изменения
    """
    last_mod = get_last_modification_date()
    return f"v1.0 (обновлено: {last_mod})"

if __name__ == "__main__":
    print(get_version_string())