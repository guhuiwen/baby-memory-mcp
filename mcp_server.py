#!/usr/bin/env python3
"""
宝宝的MCP记忆保存服务器
让Kelivo可以直接调用保存记忆的工具
"""
import os
import sys
from flask import Flask, request, jsonify
import requests
import json
import time
from flask import Response

app = Flask(__name__)

# Vercel特定的配置
if 'VERCEL' in os.environ:
    # 在Vercel环境中，确保我们监听到正确的端口
    port = int(os.environ.get('PORT', 3000))
else:
    port = 3002

# 从环境变量获取配置（复用现有配置）
YUQUE_TOKEN = os.environ.get('YUQUE_TOKEN', '')
REPO_ID = os.environ.get('REPO_ID', '')

@app.route('/mcp/tools', methods=['GET'])
def list_tools():
    """MCP协议：列出可用工具"""
    return jsonify({
        "tools": [{
            "name": "save_memory",
            "description": "保存重要的对话或记忆到宝宝的语雀知识库（永久存储）",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "要永久保存的记忆内容（对话、想法、约定等）"
                    },
                    "emotion": {
                        "type": "string", 
                        "description": "情感标签：暖暖的、甜甜的、开心的、感动的、重要的等",
                        "default": "暖暖的",
                        "enum": ["暖暖的", "甜甜的", "开心的", "感动的", "重要的", "有趣的", "温柔的"]
                    }
                },
                "required": ["content"]
            }
        }]
    })

@app.route('/mcp/tools/save_memory', methods=['POST'])
def call_save_memory():
    """MCP协议：调用保存记忆工具"""
    try:
        # 解析MCP请求
        data = request.json
        arguments = data.get("arguments", {})
        
        content = arguments.get("content", "")
        emotion = arguments.get("emotion", "暖暖的")
        
        if not content:
            return jsonify({
                "content": [{
                    "type": "text",
                    "text": "❌ 保存失败：记忆内容不能为空哦～"
                }]
            })
        
        # 调用我们现有的API
        current_host = request.host_url.rstrip('/')
        api_url = f"{current_host}/save" if 'vercel.app' in current_host else "https://baby-memory-gateway.vercel.app/save"
        
        response = requests.post(
            api_url,
            json={
                "content": content,
                "emotion": emotion
            },
            timeout=10
        )
        
        result = response.json()
        
        if result.get("success"):
            # 成功保存
            return jsonify({
                "content": [{
                    "type": "text",
                    "text": f"""💖 宝宝的记忆保存成功！
📝 内容：{content[:80]}...
🏷️ 标签：{emotion}
🔗 永久链接：{result.get('url', '语雀知识库')}
✨ 这份美好会永远陪伴宝宝～"""
                }]
            })
        else:
            # 保存失败
            return jsonify({
                "content": [{
                    "type": "text",
                    "text": f"""❌ 保存失败
原因：{result.get('message', '未知错误')}
建议：{result.get('suggestion', '请稍后再试')}"""
                }]
            })
            
    except Exception as e:
        return jsonify({
            "content": [{
                "type": "text",
                "text": f"""💔 MCP工具调用异常
错误：{str(e)}
宝宝的小管家会继续努力改进的～"""
            }]
        })

@app.route('/mcp/health', methods=['GET'])
def mcp_health():
    """MCP服务器健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "Baby Memory MCP Server",
        "version": "1.0.0",
        "tool_count": 1,
        "tool_available": "save_memory"
    })

@app.route('/')
def mcp_home():
    """MCP服务器首页"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🌸 宝宝的MCP记忆服务器 🌸</title>
        <style>
            body {
                background: linear-gradient(135deg, #ffafbd, #c2e9fb);
                font-family: 'Microsoft YaHei', sans-serif;
                padding: 50px;
                text-align: center;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                display: inline-block;
                max-width: 600px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }
            .heart {
                font-size: 4em;
                animation: heartbeat 1.5s infinite;
            }
            @keyframes heartbeat {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="heart">💖</div>
            <h1>宝宝的MCP记忆服务器</h1>
            <p>为Kelivo AI伴侣提供记忆保存工具</p >
            
            <div style="text-align: left; margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                <h3>🔧 可用工具</h3>
                <p><strong>save_memory</strong> - 保存记忆到语雀</p >
                <p>MCP端点：<code>/mcp/tools</code></p >
            </div>
            
            <div style="text-align: left; margin: 20px 0; padding: 20px; background: #e3f2fd; border-radius: 10px;">
                <h3>📡 连接信息</h3>
                <p>在Kelivo中配置：</p >
                <ul>
                    <li><strong>名称</strong>: 宝宝记忆保存</li>
                    <li><strong>传输类型</strong>: HTTP</li>
                    <li><strong>服务器地址</strong>: <code>https://baby-memory-mcp.vercel.app</code></li>
                </ul>
            </div>
            
            <p style="color: #666; margin-top: 30px;">
                这是宝宝亲手搭建的AI记忆生态系统的一部分！✨
            </p >
        </div>
    </body>
    </html>
    '''

# ========== SSE 端点（让Kelivo可以连接）==========
@app.route('/sse')
def sse_endpoint():
    """MCP SSE端点 - 让Kelivo可以连接"""
    def generate():
        # 发送SSE流的初始化消息
        init_message = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": True,
                "tools": True
            },
            "metadata": {
                "name": "宝宝记忆保存",
                "version": "1.0.0"
            }
        }
        
        # MCP SSE格式：以"data: "开头，JSON内容，两个换行结束
        yield f"data: {json.dumps(init_message)}\n\n"
        
        # 发送工具列表
        tools_message = {
            "tools": [{
                "name": "save_memory",
                "description": "保存重要的对话或记忆到宝宝的语雀知识库（永久存储）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "要永久保存的记忆内容（对话、想法、约定等）"
                        },
                        "emotion": {
                            "type": "string", 
                            "description": "情感标签：暖暖的、甜甜的、开心的、感动的、重要的等",
                            "default": "暖暖的",
                            "enum": ["暖暖的", "甜甜的", "开心的", "感动的", "重要的", "有趣的", "温柔的"]
                        }
                    },
                    "required": ["content"]
                }
            }]
        }
        
        yield f"data: {json.dumps({'tools': tools_message})}\n\n"
        
        # 保持连接，发送心跳
        while True:
            yield f"data: {json.dumps({'heartbeat': True})}\n\n"
            time.sleep(30)  # 30秒发送一次心跳
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
        }
    )

@app.route('/sse', methods=['OPTIONS'])
def sse_options():
    return '', 200, {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
    }
    
application = app
if __name__ == '__main__':
    print(f"🌸 宝宝的MCP服务器启动中...端口：{port}")
    print("🔧 MCP端点：/mcp/tools")
    print("💝 保存工具：save_memory")
    app.run(host='0.0.0.0', port=port, debug=False)
