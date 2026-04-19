CHINESE_LANDING_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FAL-SH - AI智能文本摘要API | 最低只要¥0.07/千字符</title>
    <meta name="description" content="最便宜的AI文本摘要API，¥0.07/千字符，无月费，无订阅。支持中文、英文，免费试用，Stripe安全支付。">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #0a0a1a; color: #e0e0e0; min-height: 100vh; }
        .container { max-width: 900px; margin: 0 auto; padding: 40px 20px; }
        .hero { text-align: center; padding: 60px 0; }
        .hero h1 { font-size: 3.5em; font-weight: 800; background: linear-gradient(135deg, #667eea 0%, #f5576c 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 15px; }
        .hero .subtitle { font-size: 1.5em; color: #888; margin-bottom: 30px; }
        .hero .cn-tag { display: inline-block; background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%); padding: 8px 20px; border-radius: 50px; font-size: 1em; font-weight: 600; margin-bottom: 20px; color: white; }
        .price-badge { display: inline-block; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 15px 35px; border-radius: 50px; font-size: 1.4em; font-weight: 700; margin-bottom: 40px; }
        .price-badge small { font-size: 0.6em; opacity: 0.9; }
        
        .demo-box { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 1px solid #2a2a4a; border-radius: 16px; padding: 30px; margin: 40px 0; }
        .demo-box h3 { color: #667eea; margin-bottom: 15px; font-size: 1.3em; }
        .demo-input { width: 100%; background: #0a0a1a; border: 1px solid #333; border-radius: 8px; padding: 15px; color: #fff; font-size: 1em; resize: vertical; min-height: 100px; margin-bottom: 15px; font-family: inherit; }
        .demo-input:focus { outline: none; border-color: #667eea; }
        .demo-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 15px 40px; border-radius: 8px; font-size: 1.1em; font-weight: 600; cursor: pointer; width: 100%; transition: transform 0.2s; }
        .demo-btn:hover { transform: scale(1.02); }
        .demo-result { margin-top: 20px; padding: 20px; background: #0a0a1a; border-radius: 8px; border-left: 4px solid #667eea; display: none; }
        .demo-result.show { display: block; }
        
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 40px 0; }
        .feature { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 1px solid #2a2a4a; border-radius: 12px; padding: 25px; }
        .feature h4 { color: #f5576c; font-size: 1.1em; margin-bottom: 8px; }
        .feature p { color: #aaa; line-height: 1.6; }
        
        .pricing { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 1px solid #2a2a4a; border-radius: 16px; padding: 40px; margin: 40px 0; text-align: center; }
        .pricing h2 { font-size: 2em; margin-bottom: 30px; }
        .pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; }
        .price-card { background: #0a0a1a; border-radius: 12px; padding: 25px; }
        .price-card .amount { font-size: 2.5em; font-weight: 700; color: #f5576c; }
        .price-card .credits { color: #888; margin: 10px 0; font-size: 0.95em; }
        .price-card .per { color: #555; font-size: 0.85em; }
        .price-card .cn { color: #667eea; font-size: 0.8em; }
        
        .payment-section { text-align: center; padding: 30px 0; }
        .payment-icons { display: flex; justify-content: center; gap: 20px; margin-top: 15px; flex-wrap: wrap; }
        .payment-icon { background: #1a1a2e; padding: 10px 20px; border-radius: 8px; font-size: 0.9em; color: #888; }
        
        .code-example { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 12px; padding: 25px; margin: 20px 0; font-family: 'Monaco', 'Consolas', monospace; font-size: 0.9em; overflow-x: auto; }
        .code-example .comment { color: #6a9955; }
        .code-example .keyword { color: #c586c0; }
        .code-example .string { color: #ce9178; }
        
        .stats { display: flex; justify-content: center; gap: 50px; margin: 40px 0; flex-wrap: wrap; }
        .stat { text-align: center; }
        .stat .number { font-size: 2.5em; font-weight: 700; color: #667eea; }
        .stat .label { color: #888; font-size: 0.9em; margin-top: 5px; }
        
        .cta-section { text-align: center; padding: 40px 0; }
        .cta-btn { display: inline-block; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; text-decoration: none; padding: 18px 50px; border-radius: 50px; font-size: 1.2em; font-weight: 700; margin: 10px; transition: transform 0.2s; }
        .cta-btn:hover { transform: scale(1.05); }
        .cta-btn.secondary { background: transparent; border: 2px solid #667eea; color: #667eea; }
        
        .use-cases { margin: 40px 0; }
        .use-cases h3 { font-size: 1.5em; margin-bottom: 20px; text-align: center; }
        .use-case-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .use-case { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 10px; padding: 20px; text-align: center; }
        .use-case .icon { font-size: 2em; margin-bottom: 10px; }
        .use-case .title { color: #667eea; font-weight: 600; }
        .use-case .desc { color: #888; font-size: 0.85em; margin-top: 5px; }
        
        .lang-switch { text-align: right; padding: 20px; }
        .lang-switch a { color: #667eea; text-decoration: none; font-size: 0.9em; }
        
        footer { text-align: center; padding: 40px 0; color: #555; border-top: 1px solid #1a1a2a; margin-top: 40px; }
        footer a { color: #667eea; text-decoration: none; }
        
        @media (max-width: 600px) {
            .hero h1 { font-size: 2.5em; }
            .stats { gap: 30px; }
            .price-badge { font-size: 1.1em; padding: 12px 25px; }
        }
    </style>
</head>
<body>
    <div class="lang-switch">
        <a href="/">English</a>
    </div>
    
    <div class="container">
        <div class="hero">
            <div class="cn-tag">🇨🇳 中文开发者首选</div>
            <h1>FAL-SH</h1>
            <p class="subtitle">AI智能文本摘要API</p>
            <div class="price-badge">¥0.07 <small>/ 千字符</small></div>
            
            <div class="stats">
                <div class="stat"><div class="number">4</div><div class="label">摘要模式</div></div>
                <div class="stat"><div class="number">中英</div><div class="label">原生支持</div></div>
                <div class="stat"><div class="number">100</div><div class="label">免费试用</div></div>
                <div class="stat"><div class="number">0</div><div class="label">月费</div></div>
            </div>
        </div>

        <div class="demo-box">
            <h3>🚀 在线体验 - 输入文本立即摘要</h3>
            <textarea class="demo-input" id="demoText" placeholder="在此输入要摘要的文本...（至少50个字符）">人工智能正在改变企业的运营方式。从自动化日常任务到通过数据分析提供深度洞察，AI工具已成为各类公司必备的解决方案。中小企业现在可以通过经济实惠的API获取强大的AI能力，与大型竞争对手站在同一起跑线上。成功采用AI的关键在于选择能无缝融入现有工作流程的工具。从小处着手，衡量效果，当看到实际效益时再逐步扩大。</textarea>
            <button class="demo-btn" onclick="runDemo()">🔍 智能摘要</button>
            <div class="demo-result" id="demoResult"></div>
        </div>

        <div class="features">
            <div class="feature">
                <h4>⚡ 4种摘要模式</h4>
                <p>自动提取、要点列表、简短摘要、段落摘要。多种输出格式满足不同场景需求。</p>
            </div>
            <div class="feature">
                <h4>🌏 中文优先</h4>
                <p>原生中文支持，自动检测语言，精准处理中文文本摘要。</p>
            </div>
            <div class="feature">
                <h4>📦 批量处理</h4>
                <p>一次最多处理10条文本，批量处理享受8折优惠。</p>
            </div>
            <div class="feature">
                <h4>💳 简单计费</h4>
                <p>按实际使用量计费，无月费无订阅。人民币定价，中国开发者友好。</p>
            </div>
        </div>

        <div class="pricing">
            <h2>透明定价 · 简单实惠</h2>
            <div class="pricing-grid">
                <div class="price-card">
                    <div class="amount">免费</div>
                    <div class="credits">100 credits</div>
                    <div class="per">无需信用卡</div>
                    <div class="cn">新用户赠送</div>
                </div>
                <div class="price-card">
                    <div class="amount">¥70</div>
                    <div class="credits">1,000 credits</div>
                    <div class="per">¥0.07/千字符</div>
                    <div class="cn">约处理100万字符</div>
                </div>
                <div class="price-card">
                    <div class="amount">¥700</div>
                    <div class="credits">10,000 credits</div>
                    <div class="per">¥0.07/千字符</div>
                    <div class="cn">约处理1000万字符</div>
                </div>
                <div class="price-card">
                    <div class="amount">¥7000</div>
                    <div class="credits">100,000 credits</div>
                    <div class="per">¥0.07/千字符</div>
                    <div class="cn">企业级套餐</div>
                </div>
            </div>
        </div>

        <div class="payment-section">
            <p style="color: #888; margin-bottom: 10px;">支付方式</p>
            <div class="payment-icons">
                <div class="payment-icon">💳 信用卡</div>
                <div class="payment-icon">📱 支付宝</div>
                <div class="payment-icon">💬 微信支付</div>
                <div class="payment-icon">🎯 Stripe安全支付</div>
            </div>
        </div>

        <div class="use-cases">
            <h3>适用场景</h3>
            <div class="use-case-grid">
                <div class="use-case">
                    <div class="icon">📰</div>
                    <div class="title">内容平台</div>
                    <div class="desc">文章自动摘要，提升阅读体验</div>
                </div>
                <div class="use-case">
                    <div class="icon">📱</div>
                    <div class="title">新闻聚合</div>
                    <div class="desc">快速处理大量新闻内容</div>
                </div>
                <div class="use-case">
                    <div class="icon">📚</div>
                    <div class="title">文档处理</div>
                    <div class="desc">长文本自动压缩提取关键信息</div>
                </div>
                <div class="use-case">
                    <div class="icon">🤖</div>
                    <div class="title">AI应用开发</div>
                    <div class="desc">为AI助手集成摘要能力</div>
                </div>
                <div class="use-case">
                    <div class="icon">📊</div>
                    <div class="title">数据分析</div>
                    <div class="desc">批量分析文本数据</div>
                </div>
                <div class="use-case">
                    <div class="icon">🎓</div>
                    <div class="title">学术研究</div>
                    <div class="desc">快速理解论文要点</div>
                </div>
            </div>
        </div>

        <h2 style="margin: 40px 0 20px;">快速开始</h2>
        <div class="code-example">
            <span class="comment"># 1. 获取免费API密钥</span><br>
            <span class="keyword">curl</span> -X POST https://ai-summarizer-api-gswm.onrender.com/keys \<br>
            &nbsp;&nbsp;-H <span class="string">"Content-Type: application/json"</span> \<br>
            &nbsp;&nbsp;-d <span class="string">'{"name":"张三","email":"zhangsan@example.com"}'</span><br><br>
            <span class="comment"># 2. 调用摘要接口</span><br>
            <span class="keyword">curl</span> -X POST https://ai-summarizer-api-gswm.onrender.com/summarize \<br>
            &nbsp;&nbsp;-H <span class="string">"Authorization: Bearer YOUR_API_KEY"</span> \<br>
            &nbsp;&nbsp;-H <span class="string">"Content-Type: application/json"</span> \<br>
            &nbsp;&nbsp;-d <span class="string">'{"text":"您的文本...","max_length":100,"mode":"auto"}'</span>
        </div>

        <div class="cta-section">
            <a href="/docs" class="cta-btn">📖 查看完整文档</a>
            <a href="javascript:void(0)" onclick="document.getElementById('demoText').focus();" class="cta-btn secondary">⚡ 立即试用</a>
        </div>
    </div>

    <script>
        async function runDemo() {
            const text = document.getElementById('demoText').value;
            const result = document.getElementById('demoResult');
            
            if (text.length < 50) {
                result.innerHTML = '<strong style="color:#f5576c;">⚠️ 请输入至少50个字符</strong>';
                result.classList.add('show');
                return;
            }
            
            result.innerHTML = '<strong style="color:#667eea;">⏳ 处理中...</strong>';
            result.classList.add('show');
            
            try {
                const response = await fetch('/summarize', {
                    method: 'POST',
                    headers: {
                        'Authorization': 'Bearer fal_demo_abc123xyz789',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        text: text,
                        max_length: 100,
                        mode: 'auto'
                    })
                });
                const data = await response.json();
                
                if (response.ok) {
                    result.innerHTML = '<strong style="color:#4ade80;">✅ 摘要结果：</strong><br><br>' + data.summary + '<br><br><small style="color:#888;">📊 压缩率：' + Math.round(data.compression_ratio * 100) + '% | 消耗：' + data.credits_used + ' credit</small>';
                } else {
                    result.innerHTML = '<strong style="color:#f5576c;">❌ 错误：</strong> ' + (data.detail || '未知错误');
                }
            } catch (e) {
                result.innerHTML = '<strong style="color:#f5576c;">❌ 网络错误：</strong> ' + e.message;
            }
        }
    </script>
</body>
</html>
"""
