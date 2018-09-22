# coding: utf8

from OpenGL.GL import GL_COMPUTE_SHADER, GL_FRAGMENT_SHADER, GL_VERTEX_SHADER, \
    GL_SHADER_STORAGE_BUFFER, GL_SHADER_STORAGE_BARRIER_BIT, GL_LINES, GL_LINE_STRIP, \
    GL_BLEND, GL_FUNC_ADD, GL_ONE, \
    glUseProgram, glBindBufferBase, glDrawArrays, glBindVertexArray, glDispatchCompute, glMemoryBarrier, glEnable,\
    glDisable, glBlendFunc, glBlendEquation

from Buffer import prepare_float_buffer_data, initialize_buffer, dispose_buffer
from Shader import initialize_shader, initialize_program, dispose_program
from Vertex import initialize_vertex_array, dispose_vertex_array
from Random import BUFFER_LAYOUT as RANDOM_BUFFER_LAYOUT, SHADER as RANDOM_SHADER
from World import BUFFER_LAYOUT as WORLD_BUFFER_LAYOUT
from Config import RAY_COUNT, RAY_GROUP_SIZE, RAY_INIT_DX, RAY_INIT_DY, RAY_DIR_COUNT, RAY_DIR_GROUP_SIZE


BUFFER_LAYOUT = """
layout(std430, binding = {binding}) buffer RayBuffer{suffix}
{{
    float ray{suffix}_ox[{ray_count}];
    float ray{suffix}_oy[{ray_count}];
    float ray{suffix}_dx[{ray_count}];
    float ray{suffix}_dy[{ray_count}];
}};
"""

RAY_BUFFER0_LAYOUT = BUFFER_LAYOUT.format(binding=1, suffix=0, ray_count=RAY_COUNT)
RAY_BUFFER1_LAYOUT = BUFFER_LAYOUT.format(binding=2, suffix=1, ray_count=RAY_COUNT)


TRACE_COMPUTE_SHADER = """
#version 430

{world_buffer_layout}
{ray_buffer0_layout}
{ray_buffer1_layout}
{include_random_layout}
{include_random}

vec2 refract(vec2 i, vec2 n, float inv_eta)
{{
  float cosi = dot(-i, n);
  float cost2 = 1.0f - inv_eta * inv_eta * (1.0f - cosi * cosi);
  vec2 t = inv_eta * i + ((inv_eta * cosi - sqrt(abs(cost2))) * n);
  return t * vec2(cost2 > 0);
}}

vec2 reflect(vec2 i, vec2 n)
{{
  return i - 2.0 * n * dot(n, i);
}}

float fresnel_dielectric_dielectric(float eta, float cos_theta)
{{
   float sin_theta_2 = 1.0 - cos_theta * cos_theta;

   float t0 = sqrt(1 - (sin_theta_2 / (eta * eta)));
   float t1 = eta * t0;
   float t2 = eta * cos_theta;

   float rs = (cos_theta - t1) / (cos_theta + t1);
   float rp = (t0 - t2) / (t0 + t2);

   return 0.5 * (rs * rs + rp * rp);
}}

layout (local_size_x = {ray_group_size}, local_size_y = 1) in;

void main()
{{
    uint ray_index = gl_GlobalInvocationID.x;

    vec2 ray0_d0 = normalize(vec2(ray0_dx[ray_index], ray0_dy[ray_index]));
    vec2 ray0_o0 = vec2(ray0_ox[ray_index], ray0_oy[ray_index]);    
    vec2 ray0_o1 = ray0_o0 + 1e6 * ray0_d0;
        
    vec3 ray_l = cross(vec3(ray0_o0, 1.0), vec3(ray0_o1, 1.0));
    
    vec2 min_hit = ray0_o1;
    float min_dist = 1e6 * 1e6;
    vec2 min_normal = vec2(0.0, 1.0);
            
    for (uint world_line = 0; world_line < WORLD_LINE_COUNT; ++world_line)
    {{
        vec2 int_o0, int_o1;
        get_world_line(world_line << 1, int_o0, int_o1); 
        
        vec3 int_l = cross(vec3(int_o0, 1.0), vec3(int_o1, 1.0));
        vec3 hit_p = cross(ray_l, int_l);
        if (abs(hit_p.z) > 0.0)
        {{
            vec2 hit = hit_p.xy / hit_p.z;
            float dist_hit = dot(ray0_d0, hit - ray0_o0);
            if (0.0 < dist_hit && dist_hit < min_dist)
            {{
                vec2 int_d = int_o1 - int_o0;
                float len_int_d = length(int_d);
                float dist_int = dot(int_d / len_int_d, hit - int_o0);
                if (0.0 < dist_int && dist_int <= len_int_d)
                {{            
                    min_hit = hit;
                    min_dist = dist_hit;
                    min_normal = int_d.yx * vec2(-1.0, 1.0);                
                }}
            }} 
        }}
    }}
    
    vec2 ray1_d, ray1_o;
    if (true) //(random(ray_index) < 0.9)
    {{   
        min_normal = normalize(min_normal) * sign(-dot(min_normal, ray0_d0));
        ray1_d = reflect(ray0_d0, min_normal);
        ray1_o = min_hit + 1e-6 * min_normal;
    }}
    else
    {{
        min_normal = normalize(min_normal) * sign(-dot(min_normal, ray0_d0));
        ray1_d = refract(ray0_d0, min_normal, 1.2);
        ray1_o = min_hit - 1e-6 * min_normal;
    }}
    
    ray1_ox[ray_index] = ray1_o.x;
    ray1_oy[ray_index] = ray1_o.y;
    ray1_dx[ray_index] = ray1_d.x;
    ray1_dy[ray_index] = ray1_d.y;
}}
""".format(
    world_buffer_layout=WORLD_BUFFER_LAYOUT,
    ray_buffer0_layout=RAY_BUFFER0_LAYOUT,
    ray_buffer1_layout=RAY_BUFFER1_LAYOUT,
    include_random_layout=RANDOM_BUFFER_LAYOUT,
    include_random=RANDOM_SHADER,
    ray_group_size=RAY_GROUP_SIZE,
)


DISPLAY_VERTEX_SHADER = """
#version 430

{ray_buffer0_layout}

{ray_buffer1_layout}

void main()
{{
    bool is_ray0 = gl_VertexID % 2 == 0;
    int index = gl_VertexID >> 1;

    gl_Position = vec4(
        is_ray0 ? ray0_ox[index] : ray1_ox[index],
        is_ray0 ? ray0_oy[index] : ray1_oy[index],
        0.0, 1.0
    );
}}
""".format(
    ray_buffer0_layout=RAY_BUFFER0_LAYOUT,
    ray_buffer1_layout=RAY_BUFFER1_LAYOUT,
)


DISPLAY_FRAGMENT_SHADER = """
#version 430

out vec4 Color;

void main()
{
    Color = vec4(0.005); 
}
"""


RAY_DIR_BUFFER_LAYOUT = """
#define RAY_DIR_COUNT {define_ray_dir_count}

layout(std430, binding = 0) buffer RayDirBuffer
{{
    float ray_dir_weights[RAY_DIR_COUNT];
}};
""".format(
    define_ray_dir_count=RAY_DIR_COUNT
)


GATHER_COMPUTE_SHADER = """
#version 430

#define RAY_DIR_GROUP_SIZE {define_ray_dir_group_size}
#define RAY_DIR_COUNT {define_ray_dir_count}
#define RAY_COUNT {define_ray_count}

{include_ray_buffer0_layout}
{include_ray_dir_buffer_layout}

const float PI = 3.1415926535897932384626433832795;

layout (local_size_x = RAY_DIR_GROUP_SIZE, local_size_y = 1) in;

void main()
{{
    uint dir_index = gl_GlobalInvocationID.x;
    
    float dir_angle = PI * (dir_index / float(RAY_DIR_COUNT - 1));
    float dir_step = PI / (RAY_DIR_COUNT - 1);

    float ray_dir_weight = 0.0;

    for (uint ray_index = 0; ray_index < RAY_COUNT; ++ray_index)
    {{
        vec2 ray_d = normalize(vec2(ray0_dx[ray_index], ray0_dy[ray_index]));
        float ray_angle = acos(ray_d.x);
        float delta_angle = ray_angle - dir_angle;
        if (abs(delta_angle) < dir_step)    // TODO we will miss some rays
        {{
            ray_dir_weight += 1.0 / RAY_COUNT;
        }}
    }}
    
    ray_dir_weights[dir_index] = ray_dir_weight;
}}
""".format(
    define_ray_dir_group_size=RAY_DIR_GROUP_SIZE,
    define_ray_dir_count=RAY_DIR_COUNT,
    define_ray_count=RAY_COUNT,
    include_ray_buffer0_layout=RAY_BUFFER0_LAYOUT,
    include_ray_dir_buffer_layout=RAY_DIR_BUFFER_LAYOUT
)


DISPLAY_DIR_VERTEX_SHADER = """
#version 430

{include_ray_dir_buffer_layout}

const float PI = 3.1415926535897932384626433832795;

void main()
{{
    uint dir_index = gl_VertexID.x;
    
    float dir_angle = PI * (dir_index / float(RAY_DIR_COUNT - 1));
    vec2 dir_position = vec2(cos(dir_angle), sin(dir_angle)) * ray_dir_weights[dir_index];
    gl_Position = vec4(dir_position, 0.0, 1.0);
}}
""".format(
    include_ray_dir_buffer_layout=RAY_DIR_BUFFER_LAYOUT
)


DISPLAY_DIR_FRAGMENT_SHADER = """
#version 430

out vec4 Color;

void main()
{
    Color = vec4(1.0); 
}
"""


HALF_RAY_COUNT = RAY_COUNT // 2
RAY0_DATA_OX = [-0.9 + (i / HALF_RAY_COUNT) * 1.8 for i in range(HALF_RAY_COUNT)] * 2
RAY0_DATA_OY = [+0.0] * RAY_COUNT
RAY0_DATA_DX = [RAY_INIT_DX] * RAY_COUNT
RAY0_DATA_DY = [RAY_INIT_DY] * HALF_RAY_COUNT + [RAY_INIT_DY] * HALF_RAY_COUNT
RAY1_DATA_OX = [+0.0] * RAY_COUNT
RAY1_DATA_OY = [+0.0] * RAY_COUNT
RAY1_DATA_DX = [+0.0] * RAY_COUNT
RAY1_DATA_DY = [+0.0] * RAY_COUNT


class Resources(object):

    def __init__(self):

        self.trace_program = None
        self.display_program = None
        self.trace_ray0_buffer = None
        self.trace_ray1_buffer = None
        self.gather_dir_program = None
        self.display_dir_program = None
        self.display_dir_buffer = None
        self.display_vertex_array = None

    def initialize(self):

        self.trace_program = initialize_program(
            initialize_shader(GL_COMPUTE_SHADER, TRACE_COMPUTE_SHADER)
        )

        self.display_program = initialize_program(
            initialize_shader(GL_VERTEX_SHADER, DISPLAY_VERTEX_SHADER),
            initialize_shader(GL_FRAGMENT_SHADER, DISPLAY_FRAGMENT_SHADER)
        )

        ray0_buffer_data = prepare_float_buffer_data(RAY0_DATA_OX + RAY0_DATA_OY + RAY0_DATA_DX + RAY0_DATA_DY)
        ray1_buffer_data = prepare_float_buffer_data(RAY1_DATA_OX + RAY1_DATA_OY + RAY1_DATA_DX + RAY1_DATA_DY)

        self.trace_ray0_buffer = initialize_buffer(ray0_buffer_data)
        self.trace_ray1_buffer = initialize_buffer(ray1_buffer_data)

        self.gather_dir_program = initialize_program(
            initialize_shader(GL_COMPUTE_SHADER, GATHER_COMPUTE_SHADER)
        )

        self.display_dir_program = initialize_program(
            initialize_shader(GL_VERTEX_SHADER, DISPLAY_DIR_VERTEX_SHADER),
            initialize_shader(GL_FRAGMENT_SHADER, DISPLAY_DIR_FRAGMENT_SHADER)
        )

        self.display_dir_buffer = initialize_buffer(prepare_float_buffer_data([1.0] * RAY_DIR_COUNT))

        self.display_vertex_array = initialize_vertex_array()

    def dispose(self):

        self.trace_program = dispose_program(self.trace_program)
        self.display_program = dispose_program(self.display_program)
        self.trace_ray0_buffer = dispose_buffer(self.trace_ray0_buffer)
        self.trace_ray1_buffer = dispose_buffer(self.trace_ray1_buffer)
        self.gather_dir_program = dispose_program(self.gather_dir_program)
        self.display_dir_program = dispose_program(self.display_dir_program)
        self.display_dir_buffer = dispose_buffer(self.display_dir_buffer)
        self.display_vertex_array = dispose_vertex_array(self.display_vertex_array)


def trace(resources, iteration, world_buffer, random_buffer):

    glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT)
    glUseProgram(resources.trace_program)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, world_buffer)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, resources.trace_ray0_buffer if iteration % 2 == 0 else resources.trace_ray1_buffer)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, resources.trace_ray1_buffer if iteration % 2 == 0 else resources.trace_ray0_buffer)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 3, random_buffer)
    glDispatchCompute(RAY_COUNT // RAY_GROUP_SIZE, 1, 1)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 3, 0)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, 0)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, 0)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, 0)
    glUseProgram(0)


def display_lines(resources, iteration):

    glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT)
    glEnable(GL_BLEND)
    glBlendEquation(GL_FUNC_ADD)
    glBlendFunc(GL_ONE, GL_ONE)
    glBindVertexArray(resources.display_vertex_array)
    glUseProgram(resources.display_program)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, resources.trace_ray0_buffer if iteration % 2 == 0 else resources.trace_ray1_buffer)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, resources.trace_ray1_buffer if iteration % 2 == 0 else resources.trace_ray0_buffer)
    glDrawArrays(GL_LINES, 0, RAY_COUNT * 2)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, 0)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, 0)
    glUseProgram(0)
    glBindVertexArray(0)
    glDisable(GL_BLEND)


def display_directions(resources, iteration):

    glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT)
    glUseProgram(resources.gather_dir_program)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, resources.display_dir_buffer)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, resources.trace_ray0_buffer if iteration % 2 == 0 else resources.trace_ray1_buffer)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, resources.trace_ray1_buffer if iteration % 2 == 0 else resources.trace_ray0_buffer)
    glDispatchCompute(RAY_DIR_COUNT // RAY_DIR_GROUP_SIZE, 1, 1)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, 0)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, 0)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, 0)
    glUseProgram(0)

    glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT)
    glBindVertexArray(resources.display_vertex_array)
    glUseProgram(resources.display_dir_program)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, resources.display_dir_buffer)
    glDrawArrays(GL_LINE_STRIP, 0, RAY_DIR_COUNT)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, 0)
    glUseProgram(0)
    glBindVertexArray(0)
