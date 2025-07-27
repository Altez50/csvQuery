#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для демонстрации открытия файлов из командной строки
"""

import subprocess
import sys
import os

def test_command_line_opening():
    """Тестирование открытия файлов из командной строки"""
    print("🧪 Тестирование открытия файлов из командной строки...")
    
    # Проверяем наличие тестового файла
    test_file = "test_formulas_integration.xlsx"
    if not os.path.exists(test_file):
        print(f"❌ Тестовый файл {test_file} не найден")
        return False
    
    print(f"✅ Найден тестовый файл: {test_file}")
    
    # Команды для тестирования
    test_commands = [
        f"python main.py {test_file}",
        f"python src/main.py {test_file}"
    ]
    
    print("\n📋 Команды для тестирования:")
    for i, cmd in enumerate(test_commands, 1):
        print(f"  {i}. {cmd}")
    
    print("\n💡 Инструкции по тестированию:")
    print("1. Запустите любую из команд выше")
    print("2. Приложение должно открыться с загруженным Excel файлом")
    print("3. Проверьте, что файл автоматически загружен в CSV Editor")
    print("4. Убедитесь, что формулы отображаются с зеленым фоном (если включены индикаторы)")
    
    print("\n🔧 Поддерживаемые форматы файлов:")
    print("  • .xlsx - Excel файлы (новый формат)")
    print("  • .xls - Excel файлы (старый формат)")
    print("  • .csv - CSV файлы")
    
    print("\n⚠️ Примеры ошибок:")
    print("  • Несуществующий файл: python main.py nonexistent.xlsx")
    print("  • Неподдерживаемый формат: python main.py document.txt")
    
    return True

if __name__ == "__main__":
    test_command_line_opening()