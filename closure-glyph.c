#include <stdio.h>

#include <ft2build.h>
#include FT_FREETYPE_H

#include <hb.h>
#include <hb-ot.h>
#include <hb-ft.h>


int
main(int argc,
     char** argv)
{
  FT_Error ft_error;
  FT_Library ft_library;
  FT_Face ft_face;

  hb_face_t *face;
  hb_font_t *font;
  hb_set_t *lookups;
  hb_codepoint_t lookup_index;

  hb_set_t *glyphs, *copy;
  hb_codepoint_t glyph_index;

  int i;

  if (argc < 3)
  {
    fprintf(stderr, "usage: %s font-file glyph...\n", argv[0]);
    return 1;
  }

  ft_error = FT_Init_FreeType(&ft_library);
  if (ft_error)
  {
    fprintf(stderr, "Calling `FT_Init_FreeType' failed.\n");
    return 1;
  }
  ft_error = FT_New_Face(ft_library, argv[1], 0, &ft_face);
  if (ft_error)
  {
    fprintf(stderr, "Can't create face for font `%s'\n", argv[1]);
    return 1;
  }

  font = hb_ft_font_create (ft_face, NULL);
  face = hb_font_get_face (font);

  lookups = hb_set_create();
  /* Collect ALL lookups. */
  hb_ot_layout_collect_lookups(face,
                               HB_OT_TAG_GSUB,
                               NULL,
                               NULL,
                               NULL,
                               lookups);

  glyphs = hb_set_create();
  copy = hb_set_create();

  for (i = 2; i < argc; i++)
  {
    hb_codepoint_t glyph;
    if (hb_font_glyph_from_string (font, argv[i], -1, &glyph))
      hb_set_add (glyphs, glyph);
  }

  do {
    hb_set_set (copy, glyphs);
    for (lookup_index = -1; hb_set_next(lookups, &lookup_index); )
      hb_ot_layout_lookup_substitute_closure (face, lookup_index, glyphs);
  } while (!hb_set_is_equal (copy, glyphs));

  for (glyph_index = -1; hb_set_next(glyphs, &glyph_index); )
    printf("%d\n", glyph_index);

  hb_set_destroy (copy);
  hb_set_destroy (glyphs);
  hb_set_destroy (lookups);
  hb_font_destroy (font);
  FT_Done_FreeType (ft_library);

  return 0;
}
