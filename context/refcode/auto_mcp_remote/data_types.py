"""
Data types and small structures for Blender MCP remote tools.
"""

import numpy as np
import attrs
from scipy.spatial.transform import Rotation


@attrs.define
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
    location: np.ndarray = attrs.field(converter=lambda x: np.asarray(x, dtype=np.float64))
    rotation: np.ndarray = attrs.field(converter=lambda x: np.asarray(x, dtype=np.float64))
    scale: np.ndarray = attrs.field(converter=lambda x: np.asarray(x, dtype=np.float64))
    visible: bool
    
    def get_world_transform(self) -> np.ndarray:
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
    
    def set_world_transform(self, transform: np.ndarray) -> None:
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


class BlenderMCPError(Exception):
    """Custom exception for Blender MCP operations"""
    pass