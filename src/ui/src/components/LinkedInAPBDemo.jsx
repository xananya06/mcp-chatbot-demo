import React, { useState, useEffect, useRef } from 'react';

const LinkedInAPBDemo = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: {
        type: 'welcome',
        title: 'Welcome to AI Tools Intelligence Platform',
        subtitle: 'LinkedIn APB Program Showcase - Full-Stack Product Building',
        description: 'Powered by MCP (Model Context Protocol) with 25,000+ AI tools database and real-time activity scoring.',
        capabilities: [
          'Real-time tool discovery with quality scoring',
          'Cross-platform analysis (GitHub, NPM, PyPI)',
          'Enterprise-ready recommendations',
          'AI-powered trend analysis'
        ]
      },
      timestamp: new Date()
    }
  ]);

  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState('');
  const [mcpServers, setMcpServers] = useState([
    { name: 'Database', status: 'ready', lastQuery: '0.12s' },
    { name: 'Web Search', status: 'ready', lastQuery: '0.34s' },
    { name: 'Memory', status: 'ready', lastQuery: '0.08s' },
    { name: 'Sequential', status: 'ready', lastQuery: '0.21s' }
  ]);
  const [systemMetrics, setSystemMetrics] = useState({
    toolsProcessed: 25347,
    queriesPerDay: 2847,
    avgResponseTime: '0.18s',
    activityAccuracy: 96.2
  });

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Add CSS animations
  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
      }
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
    `;
    document.head.appendChild(style);
    return () => document.head.removeChild(style);
  }, []);

  const demoQueries = [
    "Find React frameworks for LinkedIn-scale applications",
    "Show me AI writing tools with activity scores above 0.8",
    "Compare JavaScript frameworks by GitHub activity", 
    "What productivity tools do successful startups use?",
    "Find enterprise-ready tools with 99.9% uptime"
  ];

  const simulateLoadingStages = async () => {
    const stages = [
      'Analyzing query intent...',
      'Querying 25,347 tools database...',
      'Cross-referencing GitHub metrics...',
      'Calculating activity scores...',
      'Synthesizing recommendations...'
    ];

    for (let i = 0; i < stages.length; i++) {
      setLoadingStage(stages[i]);
      await new Promise(resolve => setTimeout(resolve, 400));
    }
  };

  const generateMockResponse = (query) => {
    const queryLower = query.toLowerCase();
    
    if (queryLower.includes('react') || queryLower.includes('framework')) {
      return {
        type: 'tool_analysis',
        title: 'React Ecosystem Analysis - Enterprise Scale',
        query: query,
        metrics: {
          toolsAnalyzed: 147,
          highActivity: 23,
          enterpriseReady: 8,
          processingTime: '0.18s'
        },
        tools: [
          {
            name: 'React',
            website: 'https://reactjs.org',
            activityScore: 0.98,
            type: 'github_repo',
            githubStars: 224068,
            npmDownloads: '20.1M/week',
            lastCommit: '6 hours ago',
            description: 'A JavaScript library for building user interfaces. Powers Facebook, Netflix, LinkedIn.',
            tags: ['Production-Ready', 'Enterprise', 'Meta-Backed'],
            confidence: 0.97
          },
          {
            name: 'Next.js',
            website: 'https://nextjs.org',
            activityScore: 0.96,
            type: 'github_repo',
            githubStars: 125543,
            npmDownloads: '5.2M/week',
            lastCommit: '2 hours ago',
            description: 'Production-ready React framework with SSR. Perfect for LinkedIn-scale applications.',
            tags: ['SSR', 'Vercel-Backed', 'Enterprise'],
            confidence: 0.95
          },
          {
            name: 'Vite',
            website: 'https://vitejs.dev',
            activityScore: 0.93,
            type: 'github_repo',
            githubStars: 67847,
            npmDownloads: '3.8M/week',
            lastCommit: '1 day ago',
            description: 'Next generation frontend tooling. Extremely fast development experience.',
            tags: ['Build Tool', 'Fast', 'Modern'],
            confidence: 0.92
          }
        ],
        insights: [
          'React dominates with 74% developer preference',
          'Next.js shows highest enterprise adoption growth (+40% YoY)',
          'All recommended tools have >0.9 activity scores'
        ]
      };
    }

    if (queryLower.includes('ai writing') || queryLower.includes('writing tools')) {
      return {
        type: 'tool_analysis',
        title: 'AI Writing Tools - Business Impact Analysis',
        query: query,
        metrics: {
          toolsAnalyzed: 89,
          highActivity: 12,
          enterpriseReady: 6,
          processingTime: '0.24s'
        },
        tools: [
          {
            name: 'Grammarly Business',
            website: 'https://grammarly.com',
            activityScore: 0.95,
            type: 'web_application',
            users: '30M+ daily',
            pricing: '$15/user/month',
            lastUpdate: '2 days ago',
            description: 'AI-powered writing assistant. Reduces writing time by 40% for teams.',
            tags: ['Enterprise', 'Proven ROI', 'API Available'],
            confidence: 0.96
          },
          {
            name: 'Jasper',
            website: 'https://jasper.ai',
            activityScore: 0.91,
            type: 'web_application',
            users: '1M+ users',
            pricing: '$99/month',
            lastUpdate: '1 week ago',
            description: 'AI content creation platform. 5x faster content generation for marketing teams.',
            tags: ['Marketing Focus', 'High ACV', 'Enterprise'],
            confidence: 0.89
          }
        ],
        insights: [
          'AI writing market growing 25% YoY ($5.1B total)',
          '70% of LinkedIn users struggle with professional writing',
          'Enterprise adoption up 200% in 2024'
        ]
      };
    }

    // Default response
    return {
      type: 'general_analysis',
      title: 'AI Tools Intelligence Analysis',
      query: query,
      metrics: {
        toolsAnalyzed: 245,
        highActivity: 34,
        enterpriseReady: 12,
        processingTime: '0.15s'
      },
      summary: 'Analyzed your query across our comprehensive database. Found multiple relevant tools with high activity scores and enterprise readiness indicators.',
      insights: [
        'MCP integration enables real-time analysis',
        'Activity scoring provides quality transparency',
        'Cross-platform metrics ensure informed decisions'
      ]
    };
  };

  const sendMessage = async () => {
    if (!currentMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: currentMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsLoading(true);

    // Update MCP servers to show activity
    setMcpServers(prev => prev.map(server => ({
      ...server,
      status: 'active'
    })));

    // Simulate loading stages
    await simulateLoadingStages();

    // Generate response
    const response = generateMockResponse(currentMessage);
    
    const assistantMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: response,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, assistantMessage]);
    setIsLoading(false);
    setLoadingStage('');

    // Reset MCP servers
    setTimeout(() => {
      setMcpServers(prev => prev.map(server => ({
        ...server,
        status: 'ready',
        lastQuery: `0.${Math.floor(Math.random() * 50 + 10)}s`
      })));
    }, 1000);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const ActivityScoreBar = ({ score, size = 'md' }) => {
    const width = size === 'sm' ? 80 : 120;
    const height = size === 'sm' ? 6 : 8;
    
    const getColor = (score) => {
      if (score >= 0.9) return '#10b981';
      if (score >= 0.7) return '#3b82f6';
      if (score >= 0.5) return '#f59e0b';
      return '#ef4444';
    };

    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{
          width: `${width}px`,
          height: `${height}px`,
          backgroundColor: '#e5e7eb',
          borderRadius: '9999px',
          overflow: 'hidden'
        }}>
          <div style={{
            height: '100%',
            width: `${score * 100}%`,
            backgroundColor: getColor(score),
            borderRadius: '9999px',
            transition: 'all 0.5s ease-out'
          }} />
        </div>
        <span style={{
          fontWeight: '500',
          fontSize: size === 'sm' ? '12px' : '14px',
          color: '#374151'
        }}>
          {score.toFixed(2)}
        </span>
      </div>
    );
  };

  const ToolCard = ({ tool }) => (
    <div style={{
      backgroundColor: 'white',
      border: '1px solid #e5e7eb',
      borderRadius: '8px',
      padding: '16px',
      boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
      transition: 'box-shadow 0.2s',
      cursor: 'pointer'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.boxShadow = '0 1px 3px 0 rgba(0, 0, 0, 0.1)';
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <h3 style={{ fontWeight: '600', color: '#111827', margin: 0 }}>{tool.name}</h3>
            <div style={{ display: 'flex', gap: '4px' }}>
              {tool.tags?.map((tag, idx) => (
                <span key={idx} style={{
                  padding: '2px 8px',
                  backgroundColor: '#dbeafe',
                  color: '#1d4ed8',
                  fontSize: '12px',
                  borderRadius: '9999px'
                }}>
                  {tag}
                </span>
              ))}
            </div>
          </div>
          <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '8px' }}>{tool.description}</p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Activity Score</div>
          <ActivityScoreBar score={tool.activityScore} size="sm" />
        </div>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ color: '#f59e0b' }}>★</span>
          <span style={{ color: '#6b7280' }}>{tool.githubStars || tool.users}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ color: '#10b981' }}>↓</span>
          <span style={{ color: '#6b7280' }}>{tool.npmDownloads || tool.pricing}</span>
        </div>
      </div>
      
      <div style={{
        marginTop: '12px',
        paddingTop: '12px',
        borderTop: '1px solid #f3f4f6',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <a 
          href={tool.website} 
          target="_blank" 
          rel="noopener noreferrer"
          style={{
            color: '#2563eb',
            fontSize: '14px',
            fontWeight: '500',
            textDecoration: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}
        >
          <span>🌐</span>
          <span>Visit Website</span>
        </a>
        <div style={{ fontSize: '12px', color: '#6b7280' }}>
          Confidence: {(tool.confidence * 100).toFixed(0)}%
        </div>
      </div>
    </div>
  );

  const MCPServerStatus = ({ server }) => (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      padding: '6px 12px',
      borderRadius: '8px',
      backgroundColor: '#f9fafb'
    }}>
      <div style={{
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        backgroundColor: server.status === 'active' ? '#10b981' : '#9ca3af',
        animation: server.status === 'active' ? 'pulse 2s infinite' : 'none'
      }} />
      <span style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>{server.name}</span>
      <span style={{ fontSize: '12px', color: '#6b7280' }}>{server.lastQuery}</span>
    </div>
  );

  const renderMessage = (message) => {
    if (message.role === 'user') {
      return (
        <div key={message.id} style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
          <div style={{
            backgroundColor: '#2563eb',
            color: 'white',
            borderRadius: '8px',
            padding: '12px 16px',
            maxWidth: '70%'
          }}>
            <p style={{ fontSize: '14px', margin: 0 }}>{message.content}</p>
          </div>
        </div>
      );
    }

    if (message.content.type === 'welcome') {
      return (
        <div key={message.id} style={{ marginBottom: '24px' }}>
          <div style={{
            background: 'linear-gradient(to right, #eff6ff, #f0f9ff)',
            borderRadius: '12px',
            padding: '24px',
            border: '1px solid #bfdbfe'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{
                backgroundColor: '#2563eb',
                padding: '8px',
                borderRadius: '8px'
              }}>
                <span style={{ fontSize: '24px' }}>🧠</span>
              </div>
              <div>
                <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#111827', margin: 0 }}>{message.content.title}</h2>
                <p style={{ color: '#2563eb', fontWeight: '500', margin: 0 }}>{message.content.subtitle}</p>
              </div>
            </div>
            
            <p style={{ color: '#374151', marginBottom: '16px' }}>{message.content.description}</p>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
              {message.content.capabilities.map((capability, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: '#10b981' }}>✓</span>
                  <span style={{ fontSize: '14px', color: '#374151' }}>{capability}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      );
    }

    if (message.content.type === 'tool_analysis') {
      return (
        <div key={message.id} style={{ marginBottom: '24px' }}>
          <div style={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '12px',
            padding: '24px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 'bold', color: '#111827', margin: 0 }}>{message.content.title}</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '14px', color: '#6b7280' }}>
                <span>{message.content.metrics.toolsAnalyzed} tools analyzed</span>
                <span>{message.content.metrics.processingTime}</span>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2563eb' }}>{message.content.metrics.toolsAnalyzed}</div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>Tools Analyzed</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981' }}>{message.content.metrics.highActivity}</div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>High Activity</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#8b5cf6' }}>{message.content.metrics.enterpriseReady}</div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>Enterprise Ready</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f59e0b' }}>{message.content.metrics.processingTime}</div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>Response Time</div>
              </div>
            </div>

            {message.content.tools && (
              <div style={{ marginBottom: '24px' }}>
                <h4 style={{ fontWeight: '600', color: '#111827', marginBottom: '16px' }}>Recommended Tools:</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {message.content.tools.map((tool, idx) => (
                    <ToolCard key={idx} tool={tool} />
                  ))}
                </div>
              </div>
            )}

            {message.content.insights && (
              <div style={{
                backgroundColor: '#eff6ff',
                borderRadius: '8px',
                padding: '16px'
              }}>
                <h4 style={{
                  fontWeight: '600',
                  color: '#1e40af',
                  marginBottom: '8px',
                  display: 'flex',
                  alignItems: 'center'
                }}>
                  <span style={{ marginRight: '8px' }}>✨</span>
                  Key Insights
                </h4>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                  {message.content.insights.map((insight, idx) => (
                    <li key={idx} style={{
                      color: '#1e40af',
                      fontSize: '14px',
                      display: 'flex',
                      alignItems: 'center',
                      marginBottom: '4px'
                    }}>
                      <span style={{ marginRight: '8px' }}>→</span>
                      {insight}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      );
    }

    if (message.content.type === 'general_analysis') {
      return (
        <div key={message.id} style={{ marginBottom: '24px' }}>
          <div style={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '12px',
            padding: '24px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 'bold', color: '#111827', margin: 0 }}>{message.content.title}</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '14px', color: '#6b7280' }}>
                <span>{message.content.metrics.toolsAnalyzed} tools analyzed</span>
                <span>{message.content.metrics.processingTime}</span>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2563eb' }}>{message.content.metrics.toolsAnalyzed}</div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>Tools Analyzed</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981' }}>{message.content.metrics.highActivity}</div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>High Activity</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#8b5cf6' }}>{message.content.metrics.enterpriseReady}</div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>Enterprise Ready</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f59e0b' }}>{message.content.metrics.processingTime}</div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>Response Time</div>
              </div>
            </div>

            <p style={{ color: '#374151', marginBottom: '16px' }}>{message.content.summary}</p>

            {message.content.insights && (
              <div style={{
                backgroundColor: '#eff6ff',
                borderRadius: '8px',
                padding: '16px'
              }}>
                <h4 style={{
                  fontWeight: '600',
                  color: '#1e40af',
                  marginBottom: '8px',
                  display: 'flex',
                  alignItems: 'center'
                }}>
                  <span style={{ marginRight: '8px' }}>✨</span>
                  Key Insights
                </h4>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                  {message.content.insights.map((insight, idx) => (
                    <li key={idx} style={{
                      color: '#1e40af',
                      fontSize: '14px',
                      display: 'flex',
                      alignItems: 'center',
                      marginBottom: '4px'
                    }}>
                      <span style={{ marginRight: '8px' }}>→</span>
                      {insight}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      );
    }

    return (
      <div key={message.id} style={{ marginBottom: '24px' }}>
        <div style={{
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
          padding: '16px'
        }}>
          <p style={{ color: '#374151', margin: 0 }}>{JSON.stringify(message.content)}</p>
        </div>
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#f9fafb' }}>
      {/* Enhanced Header */}
      <div style={{
        backgroundColor: 'white',
        borderBottom: '1px solid #e5e7eb',
        padding: '16px 24px',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{
              background: 'linear-gradient(to right, #2563eb, #4f46e5)',
              padding: '12px',
              borderRadius: '12px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}>
              <span style={{ fontSize: '32px' }}>🧠</span>
            </div>
            <div>
              <h1 style={{ fontSize: '24px', fontWeight: 'bold', color: '#111827', margin: 0 }}>AI Tools Intelligence Platform</h1>
              <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>LinkedIn APB Demo • MCP-Powered • Full-Stack Product</p>
            </div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '4px 12px',
              backgroundColor: '#dcfce7',
              borderRadius: '9999px'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                backgroundColor: '#16a34a',
                borderRadius: '50%',
                animation: 'pulse 2s infinite'
              }} />
              <span style={{ color: '#15803d', fontSize: '12px', fontWeight: '500' }}>Live Production</span>
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '14px', fontWeight: '500', color: '#111827' }}>{systemMetrics.toolsProcessed.toLocaleString()}</div>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>Tools Indexed</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '14px', fontWeight: '500', color: '#111827' }}>{systemMetrics.queriesPerDay.toLocaleString()}</div>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>Daily Queries</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '14px', fontWeight: '500', color: '#111827' }}>{systemMetrics.avgResponseTime}</div>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>Avg Response</div>
            </div>
          </div>
        </div>

        {/* MCP Server Status */}
        <div style={{ marginTop: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>MCP Servers:</span>
            {mcpServers.map((server, idx) => (
              <MCPServerStatus key={idx} server={server} />
            ))}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280' }}>
            Model Context Protocol • Real-time Intelligence
          </div>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 24px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          {messages.map(renderMessage)}
          
          {isLoading && (
            <div style={{ marginBottom: '24px' }}>
              <div style={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '24px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                  <div style={{ animation: 'spin 1s linear infinite' }}>
                    <span style={{ fontSize: '20px' }}>🧠</span>
                  </div>
                  <span style={{ fontWeight: '500', color: '#111827' }}>Processing Query</span>
                </div>
                <div style={{ fontSize: '14px', color: '#2563eb', marginBottom: '12px' }}>{loadingStage}</div>
                <div style={{
                  width: '100%',
                  backgroundColor: '#e5e7eb',
                  borderRadius: '9999px',
                  height: '4px'
                }}>
                  <div style={{
                    backgroundColor: '#2563eb',
                    height: '4px',
                    borderRadius: '9999px',
                    width: '60%',
                    animation: 'pulse 2s infinite'
                  }} />
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Quick Prompts */}
      <div style={{ padding: '12px 24px', backgroundColor: 'white', borderTop: '1px solid #e5e7eb' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '8px' }}>
            <span style={{
              fontSize: '14px',
              color: '#6b7280',
              whiteSpace: 'nowrap',
              display: 'flex',
              alignItems: 'center',
              marginRight: '12px'
            }}>
              ⚡ Try:
            </span>
            {demoQueries.map((query, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentMessage(query)}
                style={{
                  flexShrink: 0,
                  padding: '4px 12px',
                  fontSize: '12px',
                  backgroundColor: '#dbeafe',
                  color: '#1d4ed8',
                  border: 'none',
                  borderRadius: '9999px',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = '#bfdbfe';
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = '#dbeafe';
                }}
              >
                {query}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Enhanced Input */}
      <div style={{ padding: '16px 24px', backgroundColor: 'white', borderTop: '1px solid #e5e7eb' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ display: 'flex', gap: '16px' }}>
            <div style={{ flex: 1 }}>
              <div style={{ position: 'relative' }}>
                <textarea
                  value={currentMessage}
                  onChange={(e) => setCurrentMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about AI tools, search capabilities, or request analysis..."
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: '1px solid #d1d5db',
                    borderRadius: '8px',
                    fontSize: '14px',
                    resize: 'none',
                    outline: 'none',
                    transition: 'border-color 0.2s',
                    boxSizing: 'border-box'
                  }}
                  rows="2"
                  disabled={isLoading}
                  onFocus={(e) => {
                    e.target.style.borderColor = '#2563eb';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = '#d1d5db';
                  }}
                />
              </div>
            </div>
            <button
              onClick={sendMessage}
              disabled={isLoading || !currentMessage.trim()}
              style={{
                padding: '12px 24px',
                backgroundColor: isLoading || !currentMessage.trim() ? '#9ca3af' : '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: isLoading || !currentMessage.trim() ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
              onMouseEnter={(e) => {
                if (!isLoading && currentMessage.trim()) {
                  e.target.style.backgroundColor = '#1d4ed8';
                }
              }}
              onMouseLeave={(e) => {
                if (!isLoading && currentMessage.trim()) {
                  e.target.style.backgroundColor = '#2563eb';
                }
              }}
            >
              {isLoading ? (
                <>
                  <div style={{ animation: 'spin 1s linear infinite' }}>⟳</div>
                  Processing
                </>
              ) : (
                <>
                  <span>🚀</span>
                  Analyze
                </>
              )}
            </button>
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px', fontSize: '12px', color: '#6b7280' }}>
            <span>Press Enter to send • Shift+Enter for new line</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <span>🔒 Enterprise Security</span>
              <span>⚡ Real-time Analysis</span>
              <span>🧠 MCP Powered</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LinkedInAPBDemo;