// Message.jsx with fixed accessibility issues
import React from 'react';
import ReactMarkdown from 'react-markdown';
import './Message.css';
import remarkGfm from 'remark-gfm'; // For tables, strikethrough, etc.
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

function Message({ message }) {
  const { role, content } = message;

  return (
    <div className={`message ${role === 'user' ? 'user-message' : 'assistant-message'}`}>
      <div className="message-avatar">
        {role === 'user' ? 'U' : 'A'}
      </div>
      <div className="message-content">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // Custom rendering for code blocks with syntax highlighting
            code({node, inline, className, children, ...props}) {
              const match = /language-(\w+)/.exec(className || '');
              return !inline && match ? (
                <SyntaxHighlighter
                  style={vscDarkPlus}
                  language={match[1]}
                  PreTag="div"
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              ) : (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            },
            // Make links open in new tab with proper accessibility
            a: ({node, children, ...props}) => (
              <a target="_blank" rel="noopener noreferrer" {...props}>
                {children}
              </a>
            ),
            // Add accessibility-friendly heading components
            h1: ({node, children, ...props}) => (
              <h1 className="markdown-h1" {...props}>
                {children}
              </h1>
            ),
            h2: ({node, children, ...props}) => (
              <h2 className="markdown-h2" {...props}>
                {children}
              </h2>
            ),
            h3: ({node, children, ...props}) => (
              <h3 className="markdown-h3" {...props}>
                {children}
              </h3>
            ),
            // Style lists better
            ul: ({node, children, ...props}) => (
              <ul className="markdown-ul" {...props}>
                {children}
              </ul>
            ),
            ol: ({node, children, ...props}) => (
              <ol className="markdown-ol" {...props}>
                {children}
              </ol>
            ),
            // Add styling for blockquotes
            blockquote: ({node, children, ...props}) => (
              <blockquote className="markdown-blockquote" {...props}>
                {children}
              </blockquote>
            )
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}

export default Message;