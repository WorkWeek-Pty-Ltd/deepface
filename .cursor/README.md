# DeepFace API Cursor Rules

This directory contains rules and guidelines for Cursor AI when interacting with the DeepFace API codebase.

## Rules Structure

- `.cursorrules`: Root-level file containing detailed JSON information about the codebase
- `.cursor/rules/*.mdc`: Project-specific rules in the newer Markdown format

## Available Rules

1. **deepface-api.mdc**: General rules for the DeepFace API project, including architecture, workflow, and best practices
2. **custom-threshold.mdc**: Specific rules for the custom threshold parameter implementation

## Configuration Instructions

1. In Cursor, go to Settings > General
2. Ensure "Include .cursorrules file" is enabled
3. Under Project Rules, you can enable/disable specific rule files as needed

## Maintaining Rules

When making significant changes to the codebase:

1. Update relevant rule files to reflect the new architecture or workflow
2. Consider adding new rule files for major features
3. Keep the information accurate to ensure Cursor has the correct context

## Legacy Support

The root `.cursorrules` file is provided for backward compatibility with older Cursor versions. The `.mdc` files in `.cursor/rules/` are the preferred format for newer Cursor versions.
