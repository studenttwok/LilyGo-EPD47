#ifndef _UTF8String_H_
#define _UTF8String_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <Arduino.h>

    typedef struct UTF8String
    {
        // char *char_array;
        uint32_t *codepoint_array;
        // int32_t array_length;
        int32_t number_of_codepoints;
    } UTF8String;

    UTF8String *UTF8String_create(const char *in_string, int32_t array_length);

    void UTF8String_destroy(UTF8String *utf8_string);

    int UTF8String_get_number_of_codepoints(const char *in_string);

    int UTF8String_get_codepoint_at(UTF8String *utf8_string, int index);

    int UTF8String_get_codepoints_from_string(const char *in_string, uint32_t *codepoint_array);

#ifdef __cplusplus
}
#endif

#endif
