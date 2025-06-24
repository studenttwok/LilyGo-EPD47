#include "UTF8String.h"
#include "font.c"

UTF8String *UTF8String_create(const char *in_string, int32_t array_length)
{
    if (in_string == NULL || array_length <= 0)
    {
        return NULL; // Error: Invalid input string
    }

    UTF8String *utf8_string = (UTF8String *)malloc(sizeof(UTF8String));
    if (utf8_string == NULL)
    {
        return NULL; // Error: Memory allocation failed
    }

    int number_of_codepoints = UTF8String_get_number_of_codepoints(in_string); // Calculate the number of codepoints
    utf8_string->number_of_codepoints = number_of_codepoints;

    // create codepoint array
    utf8_string->codepoint_array = (uint32_t *)malloc(number_of_codepoints * sizeof(uint32_t));

    UTF8String_get_codepoints_from_string(in_string, (uint32_t *)utf8_string->codepoint_array); // Fill the codepoint array

    return utf8_string;
}

void UTF8String_destroy(UTF8String *utf8_string)
{
    if (utf8_string != NULL)
    {
        free(utf8_string->codepoint_array);
        free(utf8_string);
    }
}
int UTF8String_get_codepoint_at(UTF8String *utf8_string, int codepoint_index)
{
    if (utf8_string == NULL || codepoint_index < 0 || codepoint_index >= utf8_string->number_of_codepoints)
    {
        return -1; // Error: Invalid UTF8String or index out of bounds
    }

    return utf8_string->codepoint_array[codepoint_index]; // Return the codepoint at the specified index
}

int UTF8String_get_number_of_codepoints(const char *in_string)
{
    if (in_string == NULL)
    {
        return -1; // Error: Invalid UTF8String
    }

    uint8_t *char_pointer = (uint8_t *)in_string;
    int number_of_codepoints = 0;
    while (1)
    {
        int32_t length = utf8_len(*char_pointer);
        if (length == 0)
        {
            break; // End of string
        }
        char_pointer += length;
        number_of_codepoints++;
    }

    return number_of_codepoints;
}

int UTF8String_get_codepoints_from_string(const char *in_string, uint32_t *codepoint_array)
{
    if (in_string == NULL || codepoint_array == NULL)
    {
        return -1; // Error: Invalid UTF8String or index out of bounds
    }

    int counter = -1;
    uint8_t *char_pointer = (uint8_t *)in_string;
    uint32_t c = 0;
    int codepoint_index = 0;

    while ((c = next_cp((uint8_t **)&char_pointer)))
    {
        counter++;
        codepoint_array[counter] = c;
    }
    return 0;
}
