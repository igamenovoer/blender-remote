# Python Control API Implementation Plan

## Overview

Implement a pythonic interface for controlling Blender remotely via the BLD Remote MCP service. This provides human-friendly APIs that wrap MCP calls, allowing programmers to control Blender from external Python processes.

## Current State Analysis

### Existing Components
- **BLD Remote MCP Service**: Operational on port 6688, supports both GUI and background modes
- **Reference Implementation**: `context/refcode/auto_mcp_remote/` provides complete API structure
- **Current Package**: `src/blender_remote/` has basic CLI and MCP server functionality

### Key Adaptations Needed
1. **Port Change**: Reference uses 9876 (BlenderAutoMCP), we need 6688 (BLD Remote MCP)
2. **Package Structure**: Adapt reference to src layout format
3. **Attrs Conventions**: Follow specified conventions from goal.md
4. **Protocol Compatibility**: Ensure compatibility with our MCP service implementation

## Implementation Strategy

### Phase 1: Core Infrastructure
**Files to Create:**
- `src/blender_remote/client.py` - BlenderMCPClient implementation
- `src/blender_remote/data_types.py` - Data structures using attrs
- `src/blender_remote/exceptions.py` - Custom exceptions

**Key Requirements:**
- Default port 6688 (BLD Remote MCP)
- Socket-based TCP communication using JSON protocol
- Error handling and timeouts
- Connection testing capabilities

### Phase 2: High-Level Managers
**Files to Create:**
- `src/blender_remote/scene_manager.py` - BlenderSceneManager implementation
- `src/blender_remote/asset_manager.py` - BlenderAssetManager implementation

**Key Features:**
- Scene object manipulation (create, delete, move, transform)
- Camera controls and rendering
- Asset library access and import
- Collection management

### Phase 3: Integration and Testing
**Files to Create:**
- Updated `src/blender_remote/__init__.py` with new exports
- `tests/python_control_api/` - Test suite for new APIs

**Integration Points:**
- Export main classes from package root
- Provide convenience factory methods
- Ensure backward compatibility

## Technical Specifications

### Data Structures (attrs conventions)
```python
@attrs.define(kw_only=True, eq=False)
class SceneObject:
    name: str
    type: str
    location: np.ndarray = attrs.field(factory=lambda: np.zeros(3))
    rotation: np.ndarray = attrs.field(factory=lambda: np.array([1, 0, 0, 0]))  # w,x,y,z
    scale: np.ndarray = attrs.field(factory=lambda: np.ones(3))
    visible: bool = True
    
    @property
    def world_transform(self) -> np.ndarray:
        """Computed 4x4 transformation matrix"""
        # Implementation here
```

### Client Architecture
```python
class BlenderMCPClient:
    def __init__(self, host: str = "localhost", port: int = 6688, timeout: float = 30.0):
        # BLD Remote MCP specific configuration
        
    def execute_command(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # JSON TCP socket communication
        
    def execute_python(self, code: str) -> str:
        # Execute code via MCP execute_code handler
```

### Manager Pattern
```python
class BlenderSceneManager:
    def __init__(self, client: BlenderMCPClient):
        self.client = client
    
    @classmethod
    def from_client(cls, client: BlenderMCPClient) -> 'BlenderSceneManager':
        return cls(client)
    
    def list_objects(self, object_type: str = None) -> List[SceneObject]:
        # High-level scene operations
```

## Implementation Details

### BlenderMCPClient Adaptations
- **Port**: Default 6688 instead of 9876
- **Protocol**: JSON TCP compatible with BLD Remote MCP service
- **Error Handling**: BlenderMCPError for service-specific errors
- **Connection Management**: Auto-detect environment, Docker support

### BlenderSceneManager Features
- **Object Operations**: Create, delete, move, transform scene objects
- **Primitive Creation**: Cubes, spheres, cylinders with proper scaling
- **Camera Control**: Position, target, render settings
- **Scene Management**: Clear scene, batch updates
- **Export Functions**: GLB export with materials and transformations

### BlenderAssetManager Features
- **Library Access**: List configured asset libraries
- **Collection Import**: Import from asset libraries
- **Catalog Management**: Browse directories and blend files
- **Asset Discovery**: Search and filter collections

## Dependencies and Requirements

### Core Dependencies
```toml
# Already in pyproject.toml
attrs = ">=23.1.0"
numpy = ">=1.24.0"
trimesh = ">=3.21.0"
scipy = ">=1.10.0"
```

### Optional Dependencies
- `PIL` for image processing
- `matplotlib` for visualization helpers

## Testing Strategy

### Unit Tests
- **Client Tests**: Connection, command execution, error handling
- **Manager Tests**: Scene operations, asset operations
- **Data Types**: Transformation matrices, object properties

### Integration Tests
- **BLD Remote MCP**: Test with actual service on port 6688
- **Blender Operations**: Verify scene modifications work correctly
- **Asset Import**: Test library access and collection import

### Test Environment
- Use `tests/python_control_api/` directory
- Create mock MCP service for unit tests
- Integration tests require running Blender with BLD Remote MCP

## Migration from Reference

### Key Changes
1. **Port Configuration**: 9876 → 6688
2. **Package Structure**: Flat reference → src layout
3. **Naming**: Keep same class names for compatibility
4. **Protocol**: Ensure JSON format matches our MCP service
5. **Error Messages**: Adapt to BLD Remote MCP specific responses

### Code Reuse Strategy
- Copy core algorithms (transformation math, GLB export)
- Adapt communication protocol for our service
- Maintain API compatibility where possible
- Add BLD Remote MCP specific optimizations

## Success Criteria

### Functional Requirements
- [x] BlenderMCPClient can connect to BLD Remote MCP service (port 6688)
- [x] Execute Python code in Blender via MCP
- [x] Scene operations (create, delete, move objects)
- [x] Camera control and rendering
- [x] Asset library access and import
- [x] GLB export with materials

### Quality Requirements
- [x] Comprehensive error handling
- [x] Type hints and documentation
- [x] Attrs conventions followed
- [x] Test coverage > 80%
- [x] Backward compatibility maintained

### Performance Requirements
- [x] Connection timeout < 5 seconds
- [x] Scene operations < 1 second
- [x] GLB export < 10 seconds for typical objects
- [x] Asset import < 5 seconds

## Timeline

### Phase 1 (Day 1): Core Infrastructure
- Implement BlenderMCPClient
- Create data types with attrs
- Basic connection and command execution

### Phase 2 (Day 2): High-Level APIs
- Implement BlenderSceneManager
- Implement BlenderAssetManager
- Scene operations and asset management

### Phase 3 (Day 3): Integration and Testing
- Update package exports
- Create comprehensive test suite
- Verify integration with BLD Remote MCP

## Risk Mitigation

### Technical Risks
- **Protocol Compatibility**: Test early with actual MCP service
- **Performance**: Profile critical operations, optimize if needed
- **Dependencies**: Ensure all required packages are available

### Integration Risks
- **Service Availability**: Verify BLD Remote MCP service is running
- **Blender Compatibility**: Test with different Blender versions
- **Platform Differences**: Test on different operating systems

## Documentation Requirements

### API Documentation
- Docstrings for all public methods
- Type hints for all parameters
- Usage examples in docstrings

### User Guide
- Getting started examples
- Common use cases
- Troubleshooting guide

### Developer Guide
- Architecture overview
- Extension points
- Testing procedures

## Conclusion

This implementation provides a comprehensive pythonic interface for Blender control via the BLD Remote MCP service. The design maintains compatibility with the reference implementation while adapting to our specific service architecture and requirements.

The phased approach ensures steady progress with early validation, while the testing strategy guarantees reliability and maintainability of the resulting API.