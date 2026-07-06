# Design: PM工作台集成Open WebUI对话系统（第一阶段）

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Open WebUI Frontend                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Chat Input  │  │ PM Tool     │  │ Message Renderer    │ │
│  │             │  │ Selector    │  │ (PM Data Cards)     │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────┘ │
│         │                │                                  │
│  ┌──────▼────────────────▼──────┐                          │
│  │      PM Data Service          │                          │
│  │  (Frontend API Client)        │                          │
│  └──────────────┬────────────────┘                          │
└─────────────────│───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                    Open WebUI Backend                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ PM Router   │  │ PM Tools    │  │ Tool Registry       │  │
│  │ (/api/v1/pm)│  │ (pm_*.py)   │  │ (builtin.py)        │  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────┘  │
│         │                │                                   │
│  ┌──────▼────────────────▼──────┐                            │
│  │      PM Service Layer        │                            │
│  │  (CRUD, Search, Annotation)  │                            │
│  └──────────────┬───────────────┘                            │
│                 │                                            │
│  ┌──────────────▼──────────────┐                             │
│  │      Database (SQLite/PG)    │                             │
│  │  pm_project, pm_entry,       │                             │
│  │  pm_entry_version,            │                             │
│  │  pm_annotation (new)          │                             │
│  └─────────────────────────────┘                             │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. PM 数据查询流程
```
User (Chat) → Tool Selector → PM Tool → PM API → Database
     ↑                                              │
     └────────────── Response ←─────────────────────┘
```

### 2. 标注生成流程
```
User Request → AI Tool → Query Entry Data → Generate Annotation
     ↑                                                    │
     └────────────── Save to DB ←────────────────────────┘
```

### 3. 对话引用流程
```
User Select Entry → Copy to Chat Context → AI Processes → Show Result
```

## Data Models

### PMAnnotation (New)
```python
class PMAnnotation(Base):
    __tablename__ = 'pm_annotation'
    
    id = Column(Text, primary_key=True)
    entry_id = Column(Text, ForeignKey('pm_entry.id'))
    project_id = Column(Text, ForeignKey('pm_project.id'))
    annotation_type = Column(Text)  # 'prototype', 'requirement', 'spec'
    content = Column(Text)  # Rich text content
    source_data = Column(JSON)  # Source entry data snapshot
    format_template = Column(Text, nullable=True)  # Optional format template
    created_by = Column(Text)
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)
```

## API Design

### New Endpoints

#### GET /api/v1/pm/annotations
Query annotations with filters.

**Parameters:**
- `entry_id`: Filter by entry
- `project_id`: Filter by project
- `annotation_type`: Filter by type

**Response:**
```json
{
  "items": [
    {
      "id": "...",
      "entry_id": "...",
      "content": "...",
      "annotation_type": "prototype",
      "created_at": 1234567890
    }
  ],
  "total": 10
}
```

#### POST /api/v1/pm/annotations
Create a new annotation.

**Body:**
```json
{
  "entry_id": "...",
  "annotation_type": "prototype",
  "content": "...",
  "source_data": {...}
}
```

#### GET /api/v1/pm/entries/{entry_id}/annotations
Get annotations for a specific entry.

#### POST /api/v1/pm/entries/{entry_id}/generate-annotation
Generate annotation text from entry data.

**Body:**
```json
{
  "annotation_type": "prototype",
  "format_template": "..."
}
```

**Response:**
```json
{
  "content": "Generated annotation text...",
  "format": "markdown"
}
```

## Tool Design

### pm_annotation_tool.py
New tool for annotation operations.

```python
class Tools:
    async def generate_annotation(
        self, 
        entry_id: str, 
        annotation_type: str = "prototype",
        __event_emitter__: callable = None
    ) -> str:
        """Generate annotation text from PM entry data"""
        pass
    
    async def save_annotation(
        self,
        entry_id: str,
        content: str,
        annotation_type: str = "prototype",
        __event_emitter__: callable = None
    ) -> str:
        """Save annotation to PM database"""
        pass
    
    async def list_annotations(
        self,
        project_id: str,
        entry_id: str = None,
        annotation_type: str = None
    ) -> str:
        """List annotations for a project or entry"""
        pass
```

### pm_data_tool.py (Enhanced)
Enhanced data query tool.

```python
class Tools:
    async def query_pm_data(
        self,
        project_id: str,
        module_type: str = None,
        search: str = None
    ) -> str:
        """Query PM data with filters"""
        pass
    
    async def get_entry_details(
        self,
        entry_id: str
    ) -> str:
        """Get detailed entry information"""
        pass
```

## Frontend Design

### Chat Integration Points

1. **Message Input Enhancement**
   - Add PM tool button near input area
   - Open PM data selector modal
   - Insert selected entry as reference

2. **PM Data Card Component**
   - Compact card showing entry summary
   - Expandable for full details
   - Copy button for content

3. **Annotation Display**
   - Rich text rendering
   - Copy-to-clipboard functionality
   - Source data reference

## Compatibility

- **Database**: New table `pm_annotation` added via migration
- **API**: New endpoints under `/api/v1/pm/annotations`
- **Tools**: New `pm_annotation_tool.py` registered in tool registry
- **Frontend**: New components in `src/lib/components/pm/`

## Rollback Plan

1. Database: Remove `pm_annotation` table
2. API: Remove annotation endpoints
3. Tools: Remove `pm_annotation_tool.py`
4. Frontend: Remove annotation components
