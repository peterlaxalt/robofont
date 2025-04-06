###### [Home](index.html)

---

## Search Syntax

Throughout MetricsMachine you can narrow down the glyphs or kerning pairs on display by using the application’s powerful search syntax.

Wildcards | |
---|---
`*` | Matches everything. For example, `A*` will match anything that starts with A. 
`?` | Matches one character. For example, `A?` will match anything that starts with A and is followed by exactly one character. 

Groups | |
---|---
`[` | Matches a right group name. For example, `[A*` will match any right group name that starts with A.
`]` | Matches a left group name. For example, `A*]` will match any left group name that starts with A.
`[]` | Matches a left or right group name. For example, `[A*]` will match any left or right group name that starts with A.
`{` | Finds the right group for a glyph. For example, `{A*` will match any right groups that contain glyphs that start with A.
`}` | Finds the left group for a glyph. For example, `A*}` will match any left groups that contain glyphs that start with A.
`{}` | Finds the left or right group for a glyph. For example, `{A*}` will match any left or right groups that contain glyphs that start with A.
`()` | Matches a reference group name. For example, `(A*)` will match any reference group name that starts with A.

#### Operators
Operators allow you to combine two or more sub-patterns to create intersections, unions or exclusions.

Operators | |
---|---
`and` | Creates an intersection of two sub-patterns. For example, `A* and *.alt` will give you anything starting with A and ending with .alt.
`or` | Creates a union of two patterns. For example, `A* or *.alt` will give you anything starting with A or ending with .alt.
`not` | Excludes something from a pattern. For example, `A* not *.alt` will give you anything starting with A but not anything ending with .alt.

### Kerning Pairs

When searching a list of kerning pairs you have some additional options. Searches as described above will work, but you can also search for specific pairs by using a comma as a separator. For example, if you search for `A*` you will get all pairs that contain a glyph name that starts with an A on either the left or the right. If you search for `A*, B*` you will get all pairs that contain a glyph name starting with A on the left and a glyph name starting with a B on the right. In addition to these, several variables exist for matching types of pair members.

Search | |
---|---
`all` | Matches everything.
`group` | Matches any group.
`glyph` | Matches any glyph.
`exception` |  Matches any exception.
  
For example, `A*, all` matches all pairs that have a glyph name on the left that starts with an A.

---

###### [Next: Scripting](scripting.html)