#!/bin/bash
# Script de emergencia para matar TODOS los procesos Python

echo "🚨 MATANDO TODOS LOS PROCESOS PYTHON..."
echo "=========================================="

# Mostrar procesos Python activos
echo ""
echo "📋 Procesos Python activos:"
ps aux | grep python | grep -v grep

echo ""
echo "⚠️  Matando procesos en 3 segundos..."
sleep 1
echo "3..."
sleep 1
echo "2..."
sleep 1
echo "1..."

# Matar todos los procesos Python
killall -9 python 2>/dev/null
killall -9 python3 2>/dev/null

sleep 1

echo ""
echo "✅ Procesos Python eliminados"
echo ""
echo "📋 Verificando procesos restantes:"
ps aux | grep python | grep -v grep

if [ $? -eq 0 ]; then
    echo ""
    echo "⚠️  AÚN HAY PROCESOS PYTHON ACTIVOS"
else
    echo ""
    echo "✅ No hay procesos Python activos"
fi

echo ""
echo "🔧 Si el brazo SIGUE moviéndose:"
echo "   1. Desconecta la alimentación 5V de los servos INMEDIATAMENTE"
echo "   2. Verifica conexiones PCA9685"
echo "   3. Reinicia la Raspberry Pi: sudo reboot"
