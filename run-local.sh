#!/bin/bash

echo "🚀 Lancement de l'application - Enchères du Domaine"
echo "===================================================="
echo ""

# Fonction pour nettoyer les processus en arrière-plan
cleanup() {
    echo ""
    echo "🛑 Arrêt de l'application..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Capturer Ctrl+C
trap cleanup SIGINT SIGTERM

# Vérifier que l'installation a été faite
if [ ! -d "backend/venv" ]; then
    echo "❌ Backend non configuré. Lancez d'abord: ./setup-local.sh"
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend non configuré. Lancez d'abord: ./setup-local.sh"
    exit 1
fi

# Lancer le backend
echo "🐍 Lancement du backend..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "✅ Backend lancé (PID: $BACKEND_PID)"
echo "   Logs: tail -f backend.log"

# Attendre que le backend démarre
echo "⏳ Attente du démarrage du backend..."
sleep 5

# Lancer le frontend
echo ""
echo "⚛️  Lancement du frontend..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "✅ Frontend lancé (PID: $FRONTEND_PID)"
echo "   Logs: tail -f frontend.log"

echo ""
echo "✅✅✅ Application démarrée ! ✅✅✅"
echo ""
echo "🌐 URLs d'accès:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📊 Voir les logs en temps réel:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 Pour arrêter: Appuyez sur Ctrl+C"
echo ""

# Attendre
wait
