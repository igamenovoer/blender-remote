"""
Data types and structures for Blender Remote Control Library.
"""

import numpy as np
import attrs
from typing import List, Optional, Dict, Any, Callable, Union
from scipy.spatial.transform import Rotation
from numpy.typing import NDArray

from .exceptions import BlenderRemoteError


def _convert_to_float64_array(x: Any) -> NDArray[np.float64]:
    """Convert input to float64 numpy array."""
    return np.asarray(x, dtype=np.float64)


def _convert_to_int32_array(x: Any) -> NDArray[np.int32]:
    """Convert input to int32 numpy array."""
    return np.asarray(x, dtype=np.int32)


@attrs.define(kw_only=True, eq=False)
class SceneObject:
    """
    Represents a Blender scene object with its properties.

    Attributes
    ----------
    name : str
        Object name in Blender.
    type : str
        Object type (e.g., "MESH", "CAMERA", "LIGHT").
    location : numpy.ndarray
        Object location (x, y, z).
    rotation : numpy.ndarray
        Object rotation as quaternion (w, x, y, z).
    scale : numpy.ndarray
        Object scale (x, y, z).
    visible : bool
        Visibility state.
    """

    name: str
    type: str
    location: NDArray[np.float64] = attrs.field(
        converter=_convert_to_float64_array,
        factory=lambda: np.zeros(3, dtype=np.float64),
    )
    rotation: NDArray[np.float64] = attrs.field(
        converter=_convert_to_float64_array,
        factory=lambda: np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),  # w, x, y, z
    )
    scale: NDArray[np.float64] = attrs.field(
        converter=_convert_to_float64_array,
        factory=lambda: np.ones(3, dtype=np.float64),
    )
    visible: bool = True

    @property
    def world_transform(self) -> NDArray[np.float64]:
        """
        Get the 4x4 world transformation matrix.

        Returns
        -------
        numpy.ndarray
            4x4 transformation matrix combining translation, rotation, and scale.
        """
        # Create rotation matrix from quaternion using scipy
        rotation = Rotation.from_quat(self.rotation)
        rot_matrix = rotation.as_matrix()

        # Create scale matrix
        scale_matrix = np.diag(self.scale)

        # Combine rotation and scale
        rs_matrix = rot_matrix @ scale_matrix

        # Create 4x4 transformation matrix
        transform = np.eye(4)
        transform[:3, :3] = rs_matrix
        transform[:3, 3] = self.location

        return transform

    def set_world_transform(self, transform: NDArray[np.float64]) -> None:
        """
        Set object properties from a 4x4 world transformation matrix.

        Parameters
        ----------
        transform : numpy.ndarray
            4x4 transformation matrix to decompose into location, rotation, and scale.

        Raises
        ------
        ValueError
            If transform is not a 4x4 matrix.
        """
        # Validate input
        transform = np.asarray(transform, dtype=np.float64)
        if transform.shape != (4, 4):
            raise ValueError("transform must be a 4x4 matrix")

        # Extract translation
        self.location = transform[:3, 3].copy()

        # Extract the 3x3 rotation-scale matrix
        rs_matrix = transform[:3, :3]

        # Decompose into rotation and scale using SVD
        U, s, Vt = np.linalg.svd(rs_matrix)

        # Ensure proper rotation matrix (handle reflections)
        if np.linalg.det(U) < 0:
            U[:, -1] *= -1
            s[-1] *= -1
        if np.linalg.det(Vt) < 0:
            Vt[-1, :] *= -1
            s[-1] *= -1

        # Extract scale (singular values)
        self.scale = s.copy()

        # Extract rotation matrix
        rot_matrix = U @ Vt

        # Convert rotation matrix to quaternion using scipy
        rotation = Rotation.from_matrix(rot_matrix)
        self.rotation = rotation.as_quat()

    def copy(self) -> "SceneObject":
        """
        Create a copy of this SceneObject.

        Returns
        -------
        SceneObject
            New SceneObject instance with the same properties.
        """
        return SceneObject(
            name=self.name,
            type=self.type,
            location=self.location.copy(),
            rotation=self.rotation.copy(),
            scale=self.scale.copy(),
            visible=self.visible,
        )


@attrs.define(kw_only=True, eq=False)
class AssetLibrary:
    """
    Represents a Blender asset library configuration.

    Attributes
    ----------
    name : str
        Library name.
    path : str
        Library path on filesystem.
    collections : List[str]
        Available collections in the library.
    """

    name: str
    path: str
    collections: List[str] = attrs.field(factory=list)

    @property
    def is_valid(self) -> bool:
        """
        Check if the library path exists and is accessible.

        Returns
        -------
        bool
            True if library path exists, False otherwise.
        """
        import os

        return os.path.exists(self.path) and os.path.isdir(self.path)


@attrs.define(kw_only=True, eq=False)
class AssetCollection:
    """
    Represents a collection from an asset library.

    Attributes
    ----------
    name : str
        Collection name.
    library_name : str
        Name of the library containing this collection.
    file_path : str
        Relative path to the .blend file containing this collection.
    objects : List[str]
        Objects contained in this collection.
    """

    name: str
    library_name: str
    file_path: str
    objects: List[str] = attrs.field(factory=list)


@attrs.define(kw_only=True, eq=False)
class RenderSettings:
    """
    Represents Blender render settings.

    Attributes
    ----------
    resolution : numpy.ndarray
        Render resolution (width, height).
    samples : int
        Number of samples for rendering.
    engine : str
        Render engine name.
    output_path : str
        Output file path.
    """

    resolution: NDArray[np.int32] = attrs.field(
        converter=_convert_to_int32_array,
        factory=lambda: np.array([1920, 1080], dtype=np.int32),
    )
    samples: int = 128
    engine: str = "CYCLES"
    output_path: str = ""

    @property
    def width(self) -> int:
        """Get render width."""
        return int(self.resolution[0])

    @property
    def height(self) -> int:
        """Get render height."""
        return int(self.resolution[1])

    @property
    def aspect_ratio(self) -> float:
        """Get aspect ratio (width/height)."""
        return float(self.width) / float(self.height)


@attrs.define(kw_only=True, eq=False)
class CameraSettings:
    """
    Represents camera settings and properties.

    Attributes
    ----------
    location : numpy.ndarray
        Camera location (x, y, z).
    target : numpy.ndarray
        Target point to look at (x, y, z).
    fov : float
        Field of view in degrees.
    lens : float
        Lens focal length in mm.
    """

    location: NDArray[np.float64] = attrs.field(
        converter=_convert_to_float64_array,
        factory=lambda: np.array([7.0, -7.0, 5.0], dtype=np.float64),
    )
    target: NDArray[np.float64] = attrs.field(
        converter=_convert_to_float64_array,
        factory=lambda: np.zeros(3, dtype=np.float64),
    )
    fov: float = 50.0
    lens: float = 50.0

    @property
    def direction(self) -> NDArray[np.float64]:
        """
        Get the direction vector from camera to target.

        Returns
        -------
        numpy.ndarray
            Normalized direction vector.
        """
        direction = self.target - self.location
        length = np.linalg.norm(direction)
        if length > 0:
            return direction / length
        return np.array([0.0, 0.0, -1.0])  # Default forward direction

    @property
    def distance(self) -> float:
        """
        Get the distance from camera to target.

        Returns
        -------
        float
            Distance in Blender units.
        """
        return float(np.linalg.norm(self.target - self.location))


@attrs.define(kw_only=True, eq=False)
class MaterialSettings:
    """
    Represents material properties.

    Attributes
    ----------
    name : str
        Material name.
    color : numpy.ndarray
        Base color (r, g, b, a).
    metallic : float
        Metallic value (0.0 to 1.0).
    roughness : float
        Roughness value (0.0 to 1.0).
    emission : numpy.ndarray
        Emission color (r, g, b).
    emission_strength : float
        Emission strength.
    """

    name: str
    color: NDArray[np.float64] = attrs.field(
        converter=_convert_to_float64_array,
        factory=lambda: np.array([0.8, 0.8, 0.8, 1.0], dtype=np.float64),  # r, g, b, a
    )
    metallic: float = 0.0
    roughness: float = 0.5
    emission: NDArray[np.float64] = attrs.field(
        converter=_convert_to_float64_array,
        factory=lambda: np.zeros(3, dtype=np.float64),  # r, g, b
    )
    emission_strength: float = 0.0

    @property
    def is_emissive(self) -> bool:
        """Check if material is emissive."""
        return bool(self.emission_strength > 0.0 and np.any(self.emission > 0.0))


@attrs.define(kw_only=True, eq=False)
class SceneInfo:
    """
    Represents comprehensive scene information.

    Attributes
    ----------
    objects : List[SceneObject]
        Objects in the scene.
    materials : List[MaterialSettings]
        Materials in the scene.
    camera : Optional[CameraSettings]
        Camera settings if camera exists.
    render_settings : RenderSettings
        Current render settings.
    collections : List[str]
        Collections in the scene.
    """

    objects: List[SceneObject] = attrs.field(factory=list)
    materials: List[MaterialSettings] = attrs.field(factory=list)
    camera: Optional[CameraSettings] = None
    render_settings: RenderSettings = attrs.field(factory=RenderSettings)
    collections: List[str] = attrs.field(factory=list)

    @property
    def object_count(self) -> int:
        """Get total number of objects."""
        return len(self.objects)

    @property
    def mesh_objects(self) -> List[SceneObject]:
        """Get only mesh objects."""
        return [obj for obj in self.objects if obj.type == "MESH"]

    @property
    def light_objects(self) -> List[SceneObject]:
        """Get only light objects."""
        return [obj for obj in self.objects if obj.type == "LIGHT"]

    def get_object_by_name(self, name: str) -> Optional[SceneObject]:
        """
        Get object by name.

        Parameters
        ----------
        name : str
            Object name to search for.

        Returns
        -------
        SceneObject or None
            Object if found, None otherwise.
        """
        for obj in self.objects:
            if obj.name == name:
                return obj
        return None


@attrs.define(kw_only=True, eq=False)
class ExportSettings:
    """
    Represents export settings for various formats.

    Attributes
    ----------
    format : str
        Export format (e.g., "GLB", "FBX", "OBJ").
    filepath : str
        Output file path.
    include_materials : bool
        Whether to include materials.
    include_textures : bool
        Whether to include textures.
    apply_transforms : bool
        Whether to apply transformations.
    selection_only : bool
        Whether to export only selected objects.
    """

    format: str = "GLB"
    filepath: str = ""
    include_materials: bool = True
    include_textures: bool = True
    apply_transforms: bool = True
    selection_only: bool = False

    @property
    def is_valid(self) -> bool:
        """Check if export settings are valid."""
        return bool(self.filepath and self.format)

    @property
    def file_extension(self) -> str:
        """Get appropriate file extension for format."""
        extensions = {"GLB": ".glb", "FBX": ".fbx", "OBJ": ".obj", "PLY": ".ply"}
        return extensions.get(self.format.upper(), ".dat")
