# coding: utf8

from OpenGL.GL import GL_COMPUTE_SHADER, \
    GL_SHADER_STORAGE_BUFFER, GL_SHADER_STORAGE_BARRIER_BIT, \
    glUseProgram, glBindBufferBase, glDispatchCompute, glMemoryBarrier

from Buffer import prepare_uint_buffer_data, initialize_buffer, dispose_buffer
from Shader import initialize_shader, initialize_program, dispose_program
from Config import RAY_COUNT


BUFFER_LAYOUT = """
#define MERSENNE_TWISTER_COUNT {mersenne_twister_count}

layout(std430, binding = {binding}) buffer MersenneTwister
{{
    uvec4 mt_status[MERSENNE_TWISTER_COUNT];
    uint mt_m1[MERSENNE_TWISTER_COUNT];
    uint mt_m2[MERSENNE_TWISTER_COUNT];
    uint mt_tmat[MERSENNE_TWISTER_COUNT];
}};
""".format(binding=3, mersenne_twister_count=RAY_COUNT)

SHADER = """
float random(uint generator_index)
{{
    uvec4 status = mt_status[generator_index];

    uint x = (status[0] & 0x7fffffffU) ^ status[1] ^ status[2];
    uint y = status[3];
    x ^= (x << 1);
    y ^= (y >> 1) ^ x;
    status[0] = status[1];
    status[1] = status[2];
    status[2] = x ^ (y << 10);
    status[3] = y;
    status[1] ^= -(y & 1U) & mt_m1[generator_index];
    status[2] ^= -(y & 1U) & mt_m2[generator_index];
    
    uint t0, t1;
    t0 = status[3];
    t1 = status[0] + (status[2] >> 8);
    t0 ^= t1;
    t0 ^= -(t1 & 1U) & mt_tmat[generator_index];
    
    mt_status[generator_index] = status;
    
    return t0 * (1.0f / 4294967296.0f);
}}
""".format()


INIT_SHADER = """
#version 430

{include_rand_buffer_layout}
{include_rand_shader}

layout (local_size_x = 16, local_size_y = 1) in;

void init(uint generator_index, uint seed, uint m1, uint m2, uint tmat)
{{
  uvec4 status = uvec4(seed, m1, m2, tmat);
  for (uint i = 1; i < 8; i++)
  {{
    status[i & 3] ^= i + 1812433253U * status[(i - 1) & 3] ^ (status[(i - 1) & 3] >> 30);
  }}
  
  mt_status[generator_index] = status;
  mt_m1[generator_index] = m1;
  mt_m2[generator_index] = m2;
  mt_tmat[generator_index] = tmat;
  
  for (uint i = 0; i < 12; i++)
  {{
    random(generator_index);
  }}
}}

void main()
{{
    uint generator_index = gl_GlobalInvocationID.x;
    init(generator_index, 234340U ^ generator_index, 0xf50a1d49U, 0xffa8ffebU, 0x0bf2bfffU);  
}}
""".format(include_rand_buffer_layout=BUFFER_LAYOUT, include_rand_shader=SHADER)


class Resources(object):

    def __init__(self):

        self.init_program = None
        self.seed_buffer = None

    def initialize(self):

        self.init_program = initialize_program(initialize_shader(GL_COMPUTE_SHADER, INIT_SHADER))
        self.seed_buffer = initialize_buffer(prepare_uint_buffer_data([0] * 7 * RAY_COUNT))

    def dispose(self):

        self.init_program = dispose_program(self.init_program)
        self.seed_buffer = dispose_buffer(self.seed_buffer)


def init(resources):

    glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT)
    glUseProgram(resources.init_program)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 3, resources.seed_buffer)
    glDispatchCompute(RAY_COUNT // 16, 1, 1)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 3, 0)
    glUseProgram(0)
