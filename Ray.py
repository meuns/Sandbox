# coding: utf8

from OpenGL.GL import GL_COMPUTE_SHADER, GL_FRAGMENT_SHADER, GL_VERTEX_SHADER, \
    GL_SHADER_STORAGE_BUFFER, GL_SHADER_STORAGE_BARRIER_BIT, GL_LINES, GL_LINE_STRIP, \
    GL_BLEND, GL_FUNC_ADD, GL_ONE, \
    glUseProgram, glBindBufferBase, glDrawArrays, glBindVertexArray, glDispatchCompute, glMemoryBarrier, glEnable,\
    glDisable, glBlendFunc, glBlendEquation, glUniform1ui

from Buffer import prepare_float_buffer_data, initialize_buffer, dispose_buffer
from Shader import initialize_shader, initialize_program, dispose_program
from Vertex import initialize_vertex_array, dispose_vertex_array
from Random import BUFFER_LAYOUT as RANDOM_BUFFER_LAYOUT, SHADER as RANDOM_SHADER
from World import BUFFER_LAYOUT as WORLD_BUFFER_LAYOUT
from Config import RAY_COUNT, RAY_GROUP_SIZE, RAY_DIR_COUNT, RAY_DIR_GROUP_SIZE,\
    RAY0_DATA_OX, RAY0_DATA_OY, RAY0_DATA_DX, RAY0_DATA_DY
from View import update_view_projection, DATA_LAYOUT as VIEW_DATA_LAYOUT


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

layout(location=0) uniform uint iteration;

vec2 refract(vec2 i, vec2 n, float cos_theta, float inv_eta)
{{
  //float cos_theta = dot(-i, n);
  float cost2 = 1.0f - inv_eta * inv_eta * (1.0f - cos_theta * cos_theta);
  vec2 t = inv_eta * i + ((inv_eta * cos_theta - sqrt(abs(cost2))) * n);
  return t * vec2(cost2 > 0.0);
}}

vec2 reflect(vec2 i, vec2 n, float cos_theta)
{{
  return i + 2.0 * n * cos_theta; //dot(-i, n);
}}

float fresnel_dielectric_dielectric(float eta, float cos_theta) //vec2 i, vec2 n)
{{
    //float cos_theta = dot(-i, n);
    float sin_theta_2 = 1.0 - cos_theta * cos_theta;
    
    float t0 = sqrt(1.0 - (sin_theta_2 / (eta * eta)));
    float t1 = eta * t0;
    float t2 = eta * cos_theta;
    
    float rs = (cos_theta - t1) / (cos_theta + t1);
    float rp = (t0 - t2) / (t0 + t2);
    
    return 0.5 * (rs * rs + rp * rp);
}}

float pow2(float value)
{{
    return value * value;
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
    float min_dist = +1e32;
    vec2 min_normal = vec2(0.0, 1.0);
    float min_ior_i, min_ior_t;
            
    for (uint world_line = 0; world_line < WORLD_LINE_COUNT; ++world_line)
    {{
        vec2 int_o0, int_o1;
        float ior_i, ior_t;
        get_world_line(world_line, int_o0, int_o1, ior_i, ior_t); 
        
        vec3 int_l = cross(vec3(int_o0, 1.0), vec3(int_o1, 1.0));
        vec3 hit_p = cross(ray_l, int_l);
        if (abs(hit_p.z) > 0.0)
        {{
            vec2 hit = hit_p.xy / hit_p.z;
            float dist_hit = dot(ray0_d0, hit - ray0_o0);
            if (0.0 < dist_hit && dist_hit < min_dist)
            {{
                vec2 int_d = int_o1 - int_o0;
                float dist_int = dot(int_d, hit - int_o0);
                // +1e-8 is an epsilon for handling precision issues
                if (0.0 < dist_int && dist_int <= dot(int_d, int_d) + 1e-8)
                {{
                    min_hit = hit;
                    min_dist = dist_hit;
                    min_normal = int_d.yx * vec2(-1.0, 1.0);
                    min_ior_i = ior_i;
                    min_ior_t = ior_t;
                }}
            }} 
        }}
    }}
    
    vec2 ray1_d, ray1_o;
    ray1_d = ray0_d0;
    ray1_o = ray0_o1;
    
    if (min_dist < +1e32)
    {{
        min_normal = normalize(min_normal);
        
        float cos_theta = dot(min_normal, -ray0_d0);
        float eta;
        if (cos_theta < 0.0)
        {{
            min_normal = -min_normal;
            cos_theta = dot(min_normal, -ray0_d0);
            eta = min_ior_i / min_ior_t;
        }}
        else
        {{
            eta = min_ior_t / min_ior_i;
        }}
        
        float f = fresnel_dielectric_dielectric(eta, cos_theta);
        
        if (random(ray_index) < f)
        {{   
            ray1_d = reflect(ray0_d0, min_normal, cos_theta);
            ray1_o = min_hit + 1e-6 * min_normal;
        }}
        else
        {{
            ray1_d = refract(ray0_d0, min_normal, cos_theta, 1.0 / eta);
            ray1_o = min_hit - 1e-6 * min_normal;
        }}
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

{include_view_data_layout}
{include_ray_buffer0_layout}
{include_ray_buffer1_layout}

void main()
{{
    bool is_ray0 = gl_VertexID % 2 == 0;
    int index = gl_VertexID >> 1;

    vec3 position = view_projection * vec3(is_ray0 ? ray0_ox[index] : ray1_ox[index], is_ray0 ? ray0_oy[index] : ray1_oy[index], 1.0);

    gl_Position = vec4(position.xy / position.z, 0.0, 1.0);
}}
""".format(
    include_view_data_layout=VIEW_DATA_LAYOUT,
    include_ray_buffer0_layout=RAY_BUFFER0_LAYOUT,
    include_ray_buffer1_layout=RAY_BUFFER1_LAYOUT,
)


DISPLAY_FRAGMENT_SHADER = """
#version 430

out vec4 Color;

void main()
{
    Color = vec4(0.05); 
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
        if (abs(delta_angle) < dir_step && ray_d.y > 0.0)    // TODO we will miss some rays
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
    vec2 dir_position = vec2(cos(dir_angle), sin(dir_angle)) * ray_dir_weights[dir_index] * 5.0;
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
    Color = vec4(1.0, 0.0, 0.0, 1.0); 
}
"""


RAY1_DATA_OX = [+0.0] * RAY_COUNT
RAY1_DATA_OY = [+0.0] * RAY_COUNT
RAY1_DATA_DX = [+0.0] * RAY_COUNT
RAY1_DATA_DY = [+0.0] * RAY_COUNT

RAY2_DATA_OX = [+0.0] * RAY_COUNT
RAY2_DATA_OY = [+0.0] * RAY_COUNT
RAY2_DATA_DX = [+0.0] * RAY_COUNT
RAY2_DATA_DY = [+0.0] * RAY_COUNT


class Resources(object):

    def __init__(self):

        self.trace_program = None
        self.display_program = None
        self.trace_ray0_buffer = None
        self.trace_ray1_buffer = None
        self.trace_ray2_buffer = None
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
        ray2_buffer_data = prepare_float_buffer_data(RAY2_DATA_OX + RAY2_DATA_OY + RAY2_DATA_DX + RAY2_DATA_DY)

        self.trace_ray0_buffer = initialize_buffer(ray0_buffer_data)
        self.trace_ray1_buffer = initialize_buffer(ray1_buffer_data)
        self.trace_ray2_buffer = initialize_buffer(ray2_buffer_data)

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
        self.trace_ray2_buffer = dispose_buffer(self.trace_ray2_buffer)
        self.gather_dir_program = dispose_program(self.gather_dir_program)
        self.display_dir_program = dispose_program(self.display_dir_program)
        self.display_dir_buffer = dispose_buffer(self.display_dir_buffer)
        self.display_vertex_array = dispose_vertex_array(self.display_vertex_array)


def _select_input_buffer(resources, iteration):

    if iteration == 0:
        return resources.trace_ray0_buffer  # we never mutate this buffer
    elif iteration % 2 == 0:
        return resources.trace_ray2_buffer
    else:
        return resources.trace_ray1_buffer


def _select_output_buffer(resources, iteration):

    if iteration % 2 == 0:
        return resources.trace_ray1_buffer
    else:
        return resources.trace_ray2_buffer


def trace(resources, iteration, world_buffer, random_buffer):

    glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT)
    glUseProgram(resources.trace_program)
    glUniform1ui(0, iteration)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, world_buffer)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, _select_input_buffer(resources, iteration))
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, _select_output_buffer(resources, iteration))
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 3, random_buffer)
    glDispatchCompute(RAY_COUNT // RAY_GROUP_SIZE, 1, 1)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 3, 0)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, 0)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, 0)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, 0)
    glUseProgram(0)


def display_lines(resources, view_projection, iteration):

    glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT)
    glEnable(GL_BLEND)
    glBlendEquation(GL_FUNC_ADD)
    glBlendFunc(GL_ONE, GL_ONE)
    glBindVertexArray(resources.display_vertex_array)
    glUseProgram(resources.display_program)
    update_view_projection(view_projection)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, _select_input_buffer(resources, iteration))
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, _select_output_buffer(resources, iteration))
    glDrawArrays(GL_LINES, 0, RAY_COUNT << 1)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, 0)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, 0)
    glUseProgram(0)
    glBindVertexArray(0)
    glDisable(GL_BLEND)


def display_directions(resources, iteration):

    glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT)
    glUseProgram(resources.gather_dir_program)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, resources.display_dir_buffer)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, _select_input_buffer(resources, iteration))
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, _select_output_buffer(resources, iteration))
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
