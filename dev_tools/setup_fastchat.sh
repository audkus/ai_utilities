#!/bin/bash
# FastChat Setup Script

echo "🚀 Setting up FastChat Server..."

# Check if FastChat is installed
if ! python3 -c "import fastchat" 2>/dev/null; then
    echo "📦 Installing FastChat..."
    pip install "fschat[model_worker,webui]"
fi

echo "🔧 Starting FastChat services..."

# Start controller (in background)
echo "Starting FastChat controller..."
python3 -m fastchat.serve.controller &
CONTROLLER_PID=$!
echo "Controller PID: $CONTROLLER_PID"

# Wait a moment for controller to start
sleep 3

# Start model worker (in background)  
echo "Starting FastChat model worker..."
python3 -m fastchat.serve.model_worker --model-path lmsys/vicuna-7b-v1.5 &
WORKER_PID=$!
echo "Worker PID: $WORKER_PID"

# Wait a moment for worker to start
sleep 3

# Start OpenAI API server (in background)
echo "Starting FastChat OpenAI API server..."
python3 -m fastchat.serve.openai_api_server --host localhost --port 8000 &
API_PID=$!
echo "API Server PID: $API_PID"

echo ""
echo "✅ FastChat is starting up..."
echo "📊 Controller: http://localhost:21001"
echo "🤖 Worker: Running with vicuna-7b-v1.5"  
echo "🔗 API Server: http://localhost:8000/v1"
echo ""
echo "🧪 To test FastChat:"
echo "curl http://localhost:8000/v1/models"
echo ""
echo "⏹️  To stop FastChat:"
echo "kill $CONTROLLER_PID $WORKER_PID $API_PID"
echo ""
echo "💡 Save these PIDs to stop later: $CONTROLLER_PID $WORKER_PID $API_PID"
