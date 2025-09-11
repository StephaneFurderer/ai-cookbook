# Workflow Documentation with Mermaid

## Your Current Workflow

```mermaid
graph LR
    A[Telegram Message] --> B[Security Check]
    B -->|Trusted User| C[AI Agent]
    B -->|Untrusted| D[Block & Error]
    
    C --> E[Readwise Sub-workflow]
    E --> F[Extract Article ID]
    F --> G[Fetch Readwise Content]
    G --> H[Return Article Data]
    
    H --> C
    C --> I[Generate LinkedIn Post]
    I --> J[Send to Telegram]
    
    subgraph "Sub-workflow"
        F
        G
        H
    end
    
    subgraph "Main Workflow"
        A
        B
        C
        I
        J
    end
```

## Enhanced Workflow with Database Examples

```mermaid
graph TD
    A[Telegram Message] --> B[Security Switch]
    B -->|Approved| C[AI Agent]
    B -->|Rejected| D[Stop & Error]
    
    C --> E[Readwise Tool]
    C --> F[Category Detector]
    C --> G[Example Database]
    
    E --> H[Article Content]
    F --> I[Content Category]
    G --> J[Style Examples]
    
    H --> K[AI Content Generator]
    I --> K
    J --> K
    
    K --> L[Generated Post]
    L --> M[Send to Telegram]
    
    subgraph "Readwise Integration"
        E
        H
    end
    
    subgraph "Style Learning"
        F
        G
        I
        J
    end
    
    style C fill:#e1f5fe
    style K fill:#f3e5f5
    style G fill:#fff3e0
```

## Human Approval Workflow

```mermaid
graph TD
    A[Generated Post] --> B[Human Review Step]
    B --> C{Approved?}
    
    C -->|Yes| D[Execute/Send]
    C -->|No| E[Request Revision]
    
    E --> F[AI Revision]
    F --> B
    
    D --> G[Success Response]
    E --> H[Revision Loop]
    
    subgraph "Approval Loop"
        B
        C
        E
        F
    end
    
    style B fill:#ffeb3b
    style C fill:#4caf50
    style E fill:#ff9800
```

## Database-Enhanced Architecture

```mermaid
graph LR
    subgraph "Input Processing"
        A[Telegram] --> B[Security]
        B --> C[AI Agent]
    end
    
    subgraph "Content Analysis"
        C --> D[Readwise API]
        C --> E[Category Detection]
        D --> F[Article Content]
        E --> G[Content Type]
    end
    
    subgraph "Style Database"
        H[(Examples DB)]
        H --> I[How To Examples]
        H --> J[News Examples] 
        H --> K[Story Examples]
    end
    
    subgraph "Content Generation"
        F --> L[AI Generator]
        G --> M[Select Examples]
        M --> L
        I --> M
        J --> M
        K --> M
    end
    
    subgraph "Output"
        L --> N[LinkedIn Post]
        N --> O[Telegram Response]
    end
    
    style H fill:#4db6ac
    style L fill:#ab47bc
```

## Detailed Sub-workflow Flow

```mermaid
sequenceDiagram
    participant T as Telegram
    participant A as AI Agent
    participant S as Sub-workflow
    participant R as Readwise API
    participant D as Database
    
    T->>A: Message with URL
    A->>S: Extract & Fetch Request
    
    S->>S: Extract Article ID
    S->>R: API Call with ID
    R->>S: Article Content
    S->>A: Formatted Response
    
    A->>A: Detect Category
    A->>D: Query Examples by Category
    D->>A: Style Examples
    
    A->>A: Generate Post
    A->>T: Send LinkedIn Post
```

## Error Handling Flow

```mermaid
graph TD
    A[Process Start] --> B{Valid URL?}
    B -->|No| C[Error: Invalid URL]
    B -->|Yes| D[Extract ID]
    
    D --> E{ID Found?}
    E -->|No| F[Error: No ID]
    E -->|Yes| G[Call Readwise API]
    
    G --> H{API Success?}
    H -->|No| I[Error: API Failed]
    H -->|Yes| J[Process Content]
    
    J --> K{Content Valid?}
    K -->|No| L[Error: No Content]
    K -->|Yes| M[Generate Post]
    
    C --> N[Send Error to User]
    F --> N
    I --> N
    L --> N
    
    style C fill:#f44336
    style F fill:#f44336
    style I fill:#f44336
    style L fill:#f44336
```

## Tools for Creating Mermaid Diagrams

### **1. Online Editors**
- **Mermaid Live Editor**: https://mermaid.live/
- **Draw.io**: Supports Mermaid syntax
- **GitHub/GitLab**: Native Mermaid support in markdown

### **2. Documentation Integration**
- **Notion**: Supports Mermaid blocks
- **Obsidian**: Mermaid plugin
- **VS Code**: Mermaid preview extensions

### **3. Export Options**
- PNG/SVG images
- PDF documents
- Interactive HTML

## Mermaid Syntax Cheat Sheet

### **Basic Flowchart**
```mermaid
graph TD
    A[Rectangle] --> B{Diamond}
    B -->|Yes| C[Process]
    B -->|No| D[End]
```

### **Sequence Diagram**
```mermaid
sequenceDiagram
    Alice->>Bob: Hello
    Bob-->>Alice: Hi back
```

### **Styling**
```mermaid
graph LR
    A[Node] --> B[Node]
    style A fill:#f9f,stroke:#333
    style B fill:#bbf,stroke:#333
```

## Documentation Best Practices

1. **Keep diagrams focused** - One concept per diagram
2. **Use consistent styling** - Same colors for same types
3. **Add clear labels** - Descriptive node names
4. **Include error paths** - Show what happens when things fail
5. **Version control** - Track changes to your workflow