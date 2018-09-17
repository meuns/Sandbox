# coding: utf8

from OpenGL.GL import GL_COMPUTE_SHADER, GL_FRAGMENT_SHADER, GL_VERTEX_SHADER, \
    GL_SHADER_STORAGE_BUFFER, GL_SHADER_STORAGE_BARRIER_BIT, GL_LINES, \
    GL_BLEND, GL_FUNC_ADD, GL_ONE, \
    glUseProgram, glBindBufferBase, glDrawArrays, glBindVertexArray, glDispatchCompute, glMemoryBarrier, glEnable,\
    glDisable, glBlendFunc, glBlendEquation

from Buffer import prepare_float_buffer_data, initialize_buffer, dispose_buffer
from Shader import initialize_shader, initialize_program, dispose_program


BUFFER_LAYOUT = """
#define MERSENNE_TWISTER_COUNT %d

layout(std430, binding = {binding}) buffer MersenneTwister
{
    uint4 mt_status[MERSENNE_TWISTER_COUNT];
    uint mt_m1[MERSENNE_TWISTER_COUNT];
    uint mt_m2[MERSENNE_TWISTER_COUNT];
    uint mt_tmat[MERSENNE_TWISTER_COUNT];
};
"""

RAND_SHADER = """
float random()
{{
  uint x = (mt_status[0] & 0x7fffffffU) ^ mt_status[1] ^ mt_status[2];
  uint y = mt_status[3];
  x ^= (x << 1);
  y ^= (y >> 1) ^ x;
  mt_status[0] = mt_status[1];
  mt_status[1] = mt_status[2];
  mt_status[2] = x ^ (y << 10);
  mt_status[3] = y;
  mt_status[1] ^= -(y & 1U) & mt_m1;
  mt_status[2] ^= -(y & 1U) & mt_m2;

  uint t0, t1;
  t0 = mt_status[3];
  t1 = mt_status[0] + (mt_status[2] >> 8);
  t0 ^= t1;
  t0 ^= -(t1 & 1U) & mt_tmat;

  return t0 * (1.0f / 4294967296.0f);
}}
"""


INIT_SHADER = """
{include_rand_shader}

void init(uint seed, uint m1, uint m2, uint tmat)
{{
  mt_status[0] = seed;
  mt_status[1] = m1;
  mt_status[2] = m2;
  mt_status[3] = tmat;
  mt_m1 = m1;
  mt_m2 = m2;
  mt_tmat = tmat;

  for (int i = 1; i < 8; i++)
  {{
    mt_status[i & 3] ^= uint(i) + 1812433253U * mt_status[(i - 1) & 3] ^ (mt_status[(i - 1) & 3] >> 30);
  }}
  
  for (int i = 0; i < 12; i++)
  {{
    random();
  }}
}}
""".format(include_rand_shader=RAND_SHADER)


class Resources(object):

    def __init__(self):

        self.init_program = None
        self.seed_buffer = None

    def initialize(self):

        self.init_program = initialize_program(
            initialize_shader(GL_COMPUTE_SHADER, INIT_SHADER)
        )

        self.seed_buffer = initialize_buffer(prepare_float_buffer_data())

    def dispose(self):

        self.init_program = dispose_program(self.display_line_program)
        self.seed_buffer = dispose_buffer(self.display_normal_program)


def init(resources):

    glUseProgram(resources.init_program)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 3, resources.seed_buffer)
    glDispatchCompute(1, 1, 1)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 3, 0)
    glUseProgram(0)
