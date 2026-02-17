/**
 * Custom sigma.js v3 node programs for diamond and triangle shapes.
 *
 * Diamond: a square rotated 45 degrees (point-up orientation).
 * Triangle: an equilateral triangle pointing upward.
 *
 * Both programs reuse the same vertex/fragment shaders as @sigma/node-square,
 * differing only in their CONSTANT_DATA (vertex angles).
 */

import { NodeProgram } from "sigma/rendering";
import type { NodeDisplayData, RenderParams } from "sigma/types";
import type { ProgramInfo } from "sigma/rendering";
import { floatColor } from "sigma/utils";

const { UNSIGNED_BYTE, FLOAT } = WebGLRenderingContext;

const UNIFORMS = ["u_sizeRatio", "u_correctionRatio", "u_cameraAngle", "u_matrix"] as const;

// Same shaders as @sigma/node-square — flat colored quads/tris
const VERTEX_SHADER_SOURCE = /* glsl */ `
attribute vec4 a_id;
attribute vec4 a_color;
attribute vec2 a_position;
attribute float a_size;
attribute float a_angle;

uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_cameraAngle;
uniform float u_correctionRatio;

varying vec4 v_color;

const float bias = 255.0 / 254.0;
const float sqrt_8 = sqrt(8.0);

void main() {
  float size = a_size * u_correctionRatio / u_sizeRatio * sqrt_8;
  float angle = a_angle + u_cameraAngle;
  vec2 diffVector = size * vec2(cos(angle), sin(angle));
  vec2 position = a_position + diffVector;
  gl_Position = vec4(
    (u_matrix * vec3(position, 1)).xy,
    0,
    1
  );

  #ifdef PICKING_MODE
  v_color = a_id;
  #else
  v_color = a_color;
  #endif

  v_color.a *= bias;
}
`;

const FRAGMENT_SHADER_SOURCE = /* glsl */ `
precision mediump float;

varying vec4 v_color;

void main(void) {
  gl_FragColor = v_color;
}
`;

const ATTRIBUTES = [
  { name: "a_position", size: 2, type: FLOAT },
  { name: "a_size", size: 1, type: FLOAT },
  { name: "a_color", size: 4, type: UNSIGNED_BYTE, normalized: true },
  { name: "a_id", size: 4, type: UNSIGNED_BYTE, normalized: true },
];

const CONSTANT_ATTRIBUTES = [{ name: "a_angle", size: 1, type: FLOAT }];

const PI = Math.PI;

// --- Diamond (rotated square, point at top) ---
// Vertices at 0, PI/2, PI, -PI/2 → two triangles forming a diamond
const DIAMOND_ANGLES: number[][] = [
  [0],
  [PI / 2],
  [-PI / 2],
  [PI / 2],
  [-PI / 2],
  [PI],
];

export class NodeDiamondProgram extends NodeProgram<(typeof UNIFORMS)[number]> {
  getDefinition() {
    return {
      VERTICES: 6,
      VERTEX_SHADER_SOURCE,
      FRAGMENT_SHADER_SOURCE,
      METHOD: 4 as const,
      UNIFORMS,
      ATTRIBUTES,
      CONSTANT_ATTRIBUTES,
      CONSTANT_DATA: DIAMOND_ANGLES,
    };
  }

  processVisibleItem(nodeIndex: number, startIndex: number, data: NodeDisplayData) {
    const array = this.array;
    const color = floatColor(data.color);
    array[startIndex++] = data.x;
    array[startIndex++] = data.y;
    array[startIndex++] = data.size;
    array[startIndex++] = color;
    array[startIndex++] = nodeIndex;
  }

  setUniforms(params: RenderParams, { gl, uniformLocations }: ProgramInfo) {
    const { u_sizeRatio, u_correctionRatio, u_cameraAngle, u_matrix } = uniformLocations;
    gl.uniform1f(u_sizeRatio, params.sizeRatio);
    gl.uniform1f(u_cameraAngle, params.cameraAngle);
    gl.uniform1f(u_correctionRatio, params.correctionRatio);
    gl.uniformMatrix3fv(u_matrix, false, params.matrix);
  }
}

// --- Triangle (equilateral, pointing up) ---
// Three vertices: top (PI/2), bottom-left (PI + PI/6), bottom-right (-PI/6)
const TRIANGLE_ANGLES: number[][] = [
  [PI / 2],           // top
  [PI + PI / 6],      // bottom-left
  [-PI / 6],          // bottom-right
];

export class NodeTriangleProgram extends NodeProgram<(typeof UNIFORMS)[number]> {
  getDefinition() {
    return {
      VERTICES: 3,
      VERTEX_SHADER_SOURCE,
      FRAGMENT_SHADER_SOURCE,
      METHOD: 4 as const,
      UNIFORMS,
      ATTRIBUTES,
      CONSTANT_ATTRIBUTES,
      CONSTANT_DATA: TRIANGLE_ANGLES,
    };
  }

  processVisibleItem(nodeIndex: number, startIndex: number, data: NodeDisplayData) {
    const array = this.array;
    const color = floatColor(data.color);
    array[startIndex++] = data.x;
    array[startIndex++] = data.y;
    array[startIndex++] = data.size;
    array[startIndex++] = color;
    array[startIndex++] = nodeIndex;
  }

  setUniforms(params: RenderParams, { gl, uniformLocations }: ProgramInfo) {
    const { u_sizeRatio, u_correctionRatio, u_cameraAngle, u_matrix } = uniformLocations;
    gl.uniform1f(u_sizeRatio, params.sizeRatio);
    gl.uniform1f(u_cameraAngle, params.cameraAngle);
    gl.uniform1f(u_correctionRatio, params.correctionRatio);
    gl.uniformMatrix3fv(u_matrix, false, params.matrix);
  }
}
