"""
Curated GATE CSE C Programming (Arrays & Pointers) Curriculum.
Includes 9 concepts, prerequisite edges forming a DAG, catalog of misconceptions,
and 22 technically validated questions.
"""

CONCEPTS = [
    {
        "id": "DATA_TYPES_MEM_REP",
        "name": "Data Types & Memory Representation",
        "description": "Sizes of basic types (char, int, float), byte addressability, alignment, and the address-of operator (&).",
        "default_p_init": 0.25,
        "default_p_transit": 0.15,
        "default_p_guess": 0.20,
        "default_p_slip": 0.10,
    },
    {
        "id": "ARRAYS_BASIC",
        "name": "Arrays & Contiguous Memory",
        "description": "Definition of arrays, contiguous memory allocation, element count, and storage layout.",
        "default_p_init": 0.25,
        "default_p_transit": 0.15,
        "default_p_guess": 0.20,
        "default_p_slip": 0.10,
    },
    {
        "id": "ARRAY_INDEXING",
        "name": "Array Indexing & Bounds",
        "description": "0-based indexing, valid index ranges, absence of runtime bounds checking in C, and buffer overflows.",
        "default_p_init": 0.20,
        "default_p_transit": 0.15,
        "default_p_guess": 0.20,
        "default_p_slip": 0.10,
    },
    {
        "id": "POINTER_FUNDAMENTALS",
        "name": "Pointer Fundamentals & Dereferencing",
        "description": "Pointer variable declaration, addresses, dereferencing operator (*), null pointers, and void pointers.",
        "default_p_init": 0.15,
        "default_p_transit": 0.12,
        "default_p_guess": 0.20,
        "default_p_slip": 0.12,
    },
    {
        "id": "ARRAY_POINTER_DECAY",
        "name": "Array-to-Pointer Decay",
        "description": "Implicit conversion of an array name to a pointer to its first element in expressions, except in sizeof and &.",
        "default_p_init": 0.10,
        "default_p_transit": 0.10,
        "default_p_guess": 0.20,
        "default_p_slip": 0.15,
    },
    {
        "id": "POINTER_ARITHMETIC",
        "name": "Pointer Arithmetic & Scaling",
        "description": "Adding/subtracting integers to pointers, automatic scaling by sizeof(T), and pointer subtraction (ptrdiff_t).",
        "default_p_init": 0.10,
        "default_p_transit": 0.12,
        "default_p_guess": 0.20,
        "default_p_slip": 0.12,
    },
    {
        "id": "POINTER_ARRAY_RELATION",
        "name": "Pointer and Array Equivalence & Differences",
        "description": "The rule *(a + i) == a[i] == i[a], lvalue differences (array name is not a modifiable lvalue), function parameters.",
        "default_p_init": 0.10,
        "default_p_transit": 0.10,
        "default_p_guess": 0.20,
        "default_p_slip": 0.15,
    },
    {
        "id": "MULTIDIMENSIONAL_ARRAYS",
        "name": "Multidimensional Arrays & Pointer Syntax",
        "description": "2D arrays in row-major order, type of arr[i], pointer to array T (*p)[N], and pointer arithmetic on 2D arrays.",
        "default_p_init": 0.08,
        "default_p_transit": 0.08,
        "default_p_guess": 0.20,
        "default_p_slip": 0.15,
    },
    {
        "id": "POINTER_TO_POINTER",
        "name": "Pointer to Pointer (Double Indirection)",
        "description": "Declaration of T**, modifying pointers inside functions, ragged arrays, and command line arguments (argv).",
        "default_p_init": 0.08,
        "default_p_transit": 0.08,
        "default_p_guess": 0.20,
        "default_p_slip": 0.15,
    },
]

# Prerequisite Edges: (concept_id, prerequisite_id) -> prerequisite must be learned BEFORE concept
PREREQUISITES = [
    ("ARRAYS_BASIC", "DATA_TYPES_MEM_REP"),
    ("ARRAY_INDEXING", "ARRAYS_BASIC"),
    ("POINTER_FUNDAMENTALS", "DATA_TYPES_MEM_REP"),
    ("ARRAY_POINTER_DECAY", "ARRAYS_BASIC"),
    ("ARRAY_POINTER_DECAY", "POINTER_FUNDAMENTALS"),
    ("POINTER_ARITHMETIC", "POINTER_FUNDAMENTALS"),
    ("POINTER_ARRAY_RELATION", "ARRAY_POINTER_DECAY"),
    ("POINTER_ARRAY_RELATION", "POINTER_ARITHMETIC"),
    ("POINTER_ARRAY_RELATION", "ARRAY_INDEXING"),
    ("MULTIDIMENSIONAL_ARRAYS", "POINTER_ARRAY_RELATION"),
    ("POINTER_TO_POINTER", "POINTER_FUNDAMENTALS"),
    ("POINTER_TO_POINTER", "POINTER_ARITHMETIC"),
]

MISCONCEPTIONS = [
    {
        "id": "BYTE_INCREMENT_FALLACY",
        "concept_id": "POINTER_ARITHMETIC",
        "name": "Assuming pointer addition increases raw address by 1 byte",
        "description": "Student assumes ptr + 1 simply adds 1 to the numeric memory address regardless of the pointee type.",
        "remediation_hint": "In C, (ptr + 1) scales the memory address by sizeof(*ptr) bytes. If ptr is int* on a 4-byte architecture, ptr + 1 advances the address by 4 bytes.",
    },
    {
        "id": "ARRAY_NAME_IS_POINTER_VARIABLE",
        "concept_id": "ARRAY_POINTER_DECAY",
        "name": "Confusing array name with a modifiable pointer variable",
        "description": "Student believes an array name is a pointer variable stored in memory that can be reassigned (e.g. arr = arr + 1).",
        "remediation_hint": "An array name is a constant reference / non-modifiable lvalue representing the allocated array block. It cannot be assigned to or incremented directly like a pointer variable.",
    },
    {
        "id": "SIZEOF_ARRAY_EQUALS_POINTER_SIZE",
        "concept_id": "ARRAY_POINTER_DECAY",
        "name": "Believing sizeof(array) returns pointer size",
        "description": "Student assumes sizeof(arr) always yields 4 or 8 bytes because 'arrays are just pointers'.",
        "remediation_hint": "When applied directly to an array identifier in the same scope, sizeof(arr) yields total byte size (N * sizeof(element)). Decay does not happen inside sizeof or & operators.",
    },
    {
        "id": "PRECEDENCE_DEREF_AND_POSTINCREMENT",
        "concept_id": "POINTER_FUNDAMENTALS",
        "name": "Confusing precedence between * and ++",
        "description": "Student incorrectly evaluates *ptr++ as (*ptr)++ instead of *(ptr++).",
        "remediation_hint": "Postfix ++ has higher precedence than unary *. Therefore, *ptr++ retrieves the value at the current pointer address and then increments the pointer itself.",
    },
    {
        "id": "CONFUSING_ARRAY_OF_POINTERS_WITH_POINTER_TO_ARRAY",
        "concept_id": "MULTIDIMENSIONAL_ARRAYS",
        "name": "Confusing int *arr[10] with int (*arr)[10]",
        "description": "Student treats an array of pointers identically to a pointer to an array of integers.",
        "remediation_hint": "Due to operator precedence, [] binds tighter than *. int *arr[10] is an array of 10 integer pointers. int (*arr)[10] is a pointer to an array of 10 integers.",
    },
    {
        "id": "COMMUTATIVITY_OF_INDEXING_DISBELIEF",
        "concept_id": "POINTER_ARRAY_RELATION",
        "name": "Believing i[a] is invalid syntax in C",
        "description": "Student assumes i[a] will throw a compiler error because 'the index must be inside brackets'.",
        "remediation_hint": "Because a[i] is defined precisely by the C standard as *(a + i), and addition is commutative (*(i + a)), i[a] is completely valid and equivalent in C.",
    },
    {
        "id": "DOUBLE_POINTER_EQUALS_2D_ARRAY",
        "concept_id": "POINTER_TO_POINTER",
        "name": "Assuming int** is compatible with int arr[3][3]",
        "description": "Student passes a 2D array directly to a function accepting int** expecting it to work without warnings.",
        "remediation_hint": "A 2D array allocates a single contiguous memory block where rows are stored end-to-end. An int** expects an array of memory addresses. Their memory layouts and dereferencing paths are incompatible.",
    },
    {
        "id": "OUT_OF_BOUNDS_COMPILER_ERROR_BELIEF",
        "concept_id": "ARRAY_INDEXING",
        "name": "Expecting compile-time bounds checking in C",
        "description": "Student expects accessing arr[10] on an array of size 5 to produce a compilation error.",
        "remediation_hint": "C standard does not enforce runtime or compile-time bounds checking on array indexing. Out-of-bounds access invokes Undefined Behavior (UB), often reading arbitrary memory or causing segmentation faults.",
    },
]

QUESTIONS = [
    # 1. DATA_TYPES_MEM_REP - Easy
    {
        "id": "Q_DATA_01",
        "concept_id": "DATA_TYPES_MEM_REP",
        "title": "Size of Integer Types and Address Representation",
        "problem_text": "On a 64-bit architecture where sizeof(int) = 4 and sizeof(int*) = 8, what does the following program print?",
        "code_snippet": "int x = 10;\nprintf(\"%zu %zu\\n\", sizeof(x), sizeof(&x));",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "4 4"},
            {"id": "B", "text": "4 8"},
            {"id": "C", "text": "8 8"},
            {"id": "D", "text": "8 4"}
        ],
        "correct_answer": "B",
        "canonical_explanation": "sizeof(x) evaluates to the size of the int variable which is 4 bytes. &x is the address of x, whose type is int*. On a 64-bit machine, all pointer types are 8 bytes. Hence, 4 8.",
        "difficulty": 0.2,
        "known_misconceptions": []
    },
    # 2. DATA_TYPES_MEM_REP - Medium
    {
        "id": "Q_DATA_02",
        "concept_id": "DATA_TYPES_MEM_REP",
        "title": "Address Distance & Byte Addressability",
        "problem_text": "Consider two variables declared consecutively in a block: int a; int b; Assume a is allocated at memory address 0x1000 and the compiler places b immediately after with no padding. If sizeof(int) = 4, what is the address of b?",
        "code_snippet": "int a;\nint b;",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "0x1001"},
            {"id": "B", "text": "0x1004"},
            {"id": "C", "text": "0x1008"},
            {"id": "D", "text": "0x1002"}
        ],
        "correct_answer": "B",
        "canonical_explanation": "C uses byte addressable memory. An integer occupies 4 consecutive bytes (0x1000, 0x1001, 0x1002, 0x1003). Therefore, the next available address without padding is 0x1004.",
        "difficulty": 0.4,
        "secondary_concept_ids": ["POINTER_ARITHMETIC"],
        "known_misconceptions": ["BYTE_INCREMENT_FALLACY"]
    },
    # 3. ARRAYS_BASIC - Easy
    {
        "id": "Q_ARR_01",
        "concept_id": "ARRAYS_BASIC",
        "title": "Contiguous Memory in Arrays",
        "problem_text": "Given an integer array declared as int arr[5]; where &arr[0] is at hex address 0x2000 and sizeof(int) = 4. What is the address of arr[3]?",
        "code_snippet": "int arr[5]; // &arr[0] == 0x2000",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "0x2003"},
            {"id": "B", "text": "0x200C"},
            {"id": "C", "text": "0x2006"},
            {"id": "D", "text": "0x2012"}
        ],
        "correct_answer": "B",
        "canonical_explanation": "Array elements are stored contiguously. Address of arr[i] = Base + i * sizeof(type). Address of arr[3] = 0x2000 + 3 * 4 = 0x2000 + 12 (0x0C in hex) = 0x200C.",
        "difficulty": 0.3,
        "secondary_concept_ids": ["ARRAY_INDEXING", "DATA_TYPES_MEM_REP"],
        "known_misconceptions": ["BYTE_INCREMENT_FALLACY"]
    },
    # 4. ARRAY_INDEXING - Easy
    {
        "id": "Q_IDX_01",
        "concept_id": "ARRAY_INDEXING",
        "title": "0-based Indexing Range",
        "problem_text": "An array is declared as int nums[10];. Which of the following expressions accesses the valid final element of this array according to C standard?",
        "code_snippet": "int nums[10];",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "nums[10]"},
            {"id": "B", "text": "nums[9]"},
            {"id": "C", "text": "nums[0]"},
            {"id": "D", "text": "nums.last"}
        ],
        "correct_answer": "B",
        "canonical_explanation": "In C, arrays are 0-indexed. An array of length 10 has valid indices from 0 to 9. nums[10] is one past the end and accessing it yields undefined behavior.",
        "difficulty": 0.2,
        "known_misconceptions": ["OUT_OF_BOUNDS_COMPILER_ERROR_BELIEF"]
    },
    # 5. ARRAY_INDEXING - Medium
    {
        "id": "Q_IDX_02",
        "concept_id": "ARRAY_INDEXING",
        "title": "Out-of-Bounds Behavior in C",
        "problem_text": "What does the C standard state regarding an attempt to access arr[5] when arr is declared as int arr[5]?",
        "code_snippet": "int arr[5] = {1, 2, 3, 4, 5};\nint val = arr[5];",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "Causes a mandatory compile-time error: IndexOutOfBoundsException"},
            {"id": "B", "text": "Always sets val to 0 automatically"},
            {"id": "C", "text": "Invokes Undefined Behavior; C does not perform bounds checking"},
            {"id": "D", "text": "Returns NULL safely"}
        ],
        "correct_answer": "C",
        "canonical_explanation": "The C standard specifies no runtime bounds checks for array access. Indexing past the valid bounds causes Undefined Behavior (UB).",
        "difficulty": 0.4,
        "known_misconceptions": ["OUT_OF_BOUNDS_COMPILER_ERROR_BELIEF"]
    },
    # 6. POINTER_FUNDAMENTALS - Easy
    {
        "id": "Q_PTR_01",
        "concept_id": "POINTER_FUNDAMENTALS",
        "title": "Address-of and Dereference Operators",
        "problem_text": "What is the output of the following C code snippet?",
        "code_snippet": "int a = 42;\nint *p = &a;\n*p = 99;\nprintf(\"%d\", a);",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "42"},
            {"id": "B", "text": "99"},
            {"id": "C", "text": "Garbage address"},
            {"id": "D", "text": "Compilation Error"}
        ],
        "correct_answer": "B",
        "canonical_explanation": "p holds the address of a. The dereference *p accesses the memory location of a. Assigning *p = 99 modifies the value of a directly to 99.",
        "difficulty": 0.2,
        "known_misconceptions": []
    },
    # 7. POINTER_FUNDAMENTALS - Hard
    {
        "id": "Q_PTR_02",
        "concept_id": "POINTER_FUNDAMENTALS",
        "title": "Pointer Dereference and Post-Increment Precedence",
        "problem_text": "What does the following snippet print?",
        "code_snippet": "int arr[] = {10, 20, 30};\nint *p = arr;\nint val = *p++;\nprintf(\"val=%d, *p=%d\", val, *p);",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "val=10, *p=20"},
            {"id": "B", "text": "val=11, *p=11"},
            {"id": "C", "text": "val=20, *p=20"},
            {"id": "D", "text": "val=10, *p=10"}
        ],
        "correct_answer": "A",
        "canonical_explanation": "Postfix ++ has higher precedence than *. So *p++ evaluates as *(p++). The value of expression p++ is the original pointer p, so *p yields 10 (stored in val). Side effect increments p to point to the next element (20). So *p is now 20.",
        "difficulty": 0.7,
        "known_misconceptions": ["PRECEDENCE_DEREF_AND_POSTINCREMENT"]
    },
    # 8. ARRAY_POINTER_DECAY - Easy
    {
        "id": "Q_DECAY_01",
        "concept_id": "ARRAY_POINTER_DECAY",
        "title": "Array Name Decay to Pointer",
        "problem_text": "When an array name 'arr' of type int[5] is passed to a function void foo(int *p), what happens?",
        "code_snippet": "void foo(int *p);\nint arr[5];\nfoo(arr);",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "The entire array of 5 integers is copied by value onto the call stack"},
            {"id": "B", "text": "arr implicitly decays to a pointer to its first element (&arr[0])"},
            {"id": "C", "text": "Causes a compile error because int[5] is not convertible to int*"},
            {"id": "D", "text": "A pointer to the entire array of type int(*)[5] is passed"}
        ],
        "correct_answer": "B",
        "canonical_explanation": "In C, in almost all expression contexts (except operand to sizeof and unary &), an array expression decays into a pointer to its first element.",
        "difficulty": 0.3,
        "known_misconceptions": ["ARRAY_NAME_IS_POINTER_VARIABLE"]
    },
    # 9. ARRAY_POINTER_DECAY - Medium
    {
        "id": "Q_DECAY_02",
        "concept_id": "ARRAY_POINTER_DECAY",
        "title": "sizeof Array vs sizeof Pointer",
        "problem_text": "On a platform where sizeof(int) = 4 and sizeof(int*) = 8, what is printed by the following code?",
        "code_snippet": "void func(int a[10]) {\n    printf(\"%zu \", sizeof(a));\n}\nint main() {\n    int arr[10];\n    printf(\"%zu \", sizeof(arr));\n    func(arr);\n    return 0;\n}",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "40 40"},
            {"id": "B", "text": "8 8"},
            {"id": "C", "text": "40 8"},
            {"id": "D", "text": "10 10"}
        ],
        "correct_answer": "C",
        "canonical_explanation": "In main(), arr is an array variable; sizeof(arr) evaluates to 10 * sizeof(int) = 40. In func, parameter int a[10] decays into int *a (pointer). Therefore sizeof(a) inside func yields pointer size, which is 8.",
        "difficulty": 0.6,
        "secondary_concept_ids": ["DATA_TYPES_MEM_REP"],
        "known_misconceptions": ["SIZEOF_ARRAY_EQUALS_POINTER_SIZE", "ARRAY_NAME_IS_POINTER_VARIABLE"]
    },
    # 10. ARRAY_POINTER_DECAY - Hard
    {
        "id": "Q_DECAY_03",
        "concept_id": "ARRAY_POINTER_DECAY",
        "title": "Address of Array vs Address of First Element",
        "problem_text": "Given int a[5]; consider the two pointers p1 = a and p2 = &a. While their numeric address values may print the same, how do their types differ?",
        "code_snippet": "int a[5];\n// p1 = a;\n// p2 = &a;",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "Both have identical type int*"},
            {"id": "B", "text": "p1 is int* while p2 is int (*)[5]"},
            {"id": "C", "text": "p1 is int (*)[5] while p2 is int*"},
            {"id": "D", "text": "p2 is void* by definition"}
        ],
        "correct_answer": "B",
        "canonical_explanation": "'a' decays to a pointer to the first element (type int*). '&a' does not decay; it yields a pointer to the entire array of 5 integers (type int (*)[5]).",
        "difficulty": 0.75,
        "secondary_concept_ids": ["POINTER_FUNDAMENTALS"],
        "known_misconceptions": ["SIZEOF_ARRAY_EQUALS_POINTER_SIZE", "ARRAY_NAME_IS_POINTER_VARIABLE"]
    },
    # 11. POINTER_ARITHMETIC - Easy
    {
        "id": "Q_ARITH_01",
        "concept_id": "POINTER_ARITHMETIC",
        "title": "Pointer Addition Scaling",
        "problem_text": "Suppose ptr is an int* holding address 0x3000. If sizeof(int) = 4, what address is produced by the expression (ptr + 2)?",
        "code_snippet": "int *ptr = (int*)0x3000;\nint *next = ptr + 2;",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "0x3002"},
            {"id": "B", "text": "0x3008"},
            {"id": "C", "text": "0x3004"},
            {"id": "D", "text": "0x3010"}
        ],
        "correct_answer": "B",
        "canonical_explanation": "Pointer arithmetic scales by sizeof(*ptr). Here, 0x3000 + 2 * sizeof(int) = 0x3000 + 2 * 4 = 0x3008.",
        "difficulty": 0.3,
        "known_misconceptions": ["BYTE_INCREMENT_FALLACY"]
    },
    # 12. POINTER_ARITHMETIC - Medium
    {
        "id": "Q_ARITH_02",
        "concept_id": "POINTER_ARITHMETIC",
        "title": "Pointer Subtraction",
        "problem_text": "What is the output of the following code assuming 4-byte integers?",
        "code_snippet": "int arr[5] = {10, 20, 30, 40, 50};\nint *p1 = &arr[1];\nint *p2 = &arr[4];\nprintf(\"%td\", p2 - p1);",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "12"},
            {"id": "B", "text": "3"},
            {"id": "C", "text": "4"},
            {"id": "D", "text": "Undefined Behavior"}
        ],
        "correct_answer": "B",
        "canonical_explanation": "Subtracting two pointers to elements of the same array yields the number of elements between them (ptrdiff_t), NOT the raw byte difference. Index 4 - index 1 = 3.",
        "difficulty": 0.5,
        "known_misconceptions": ["BYTE_INCREMENT_FALLACY"]
    },
    # 13. POINTER_ARITHMETIC - Hard
    {
        "id": "Q_ARITH_03",
        "concept_id": "POINTER_ARITHMETIC",
        "title": "GATE CSE Classic: Cast and Pointer Step",
        "problem_text": "What is printed by the following C program on a little-endian machine where sizeof(int) = 4?",
        "code_snippet": "int arr[] = {1, 2, 3, 4};\nchar *p = (char*)arr;\np = p + sizeof(int);\nint *q = (int*)p;\nprintf(\"%d\", *q);",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "1"},
            {"id": "B", "text": "2"},
            {"id": "C", "text": "3"},
            {"id": "D", "text": "4"}
        ],
        "correct_answer": "B",
        "canonical_explanation": "p is of type char*, so p + sizeof(int) advances the pointer by exactly 4 bytes (1 byte * 4). In arr, moving 4 bytes past the beginning advances to arr[1], which contains 2. Casting back to int* and dereferencing yields 2.",
        "difficulty": 0.8,
        "secondary_concept_ids": ["DATA_TYPES_MEM_REP", "POINTER_FUNDAMENTALS"],
        "known_misconceptions": ["BYTE_INCREMENT_FALLACY"]
    },
    # 14. POINTER_ARRAY_RELATION - Easy
    {
        "id": "Q_REL_01",
        "concept_id": "POINTER_ARRAY_RELATION",
        "title": "Equivalence of Array Indexing and Pointer Arithmetic",
        "problem_text": "According to the C standard, the expression arr[3] is defined to be identical to which of the following?",
        "code_snippet": "int arr[5];",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "*arr + 3"},
            {"id": "B", "text": "*(arr + 3)"},
            {"id": "C", "text": "&arr + 3"},
            {"id": "D", "text": "*(arr) + 3"}
        ],
        "correct_answer": "B",
        "canonical_explanation": "The subscript operator [] is defined so that E1[E2] is identical to (*((E1)+(E2))). Hence arr[3] == *(arr + 3).",
        "difficulty": 0.25,
        "known_misconceptions": []
    },
    # 15. POINTER_ARRAY_RELATION - Medium
    {
        "id": "Q_REL_02",
        "concept_id": "POINTER_ARRAY_RELATION",
        "title": "Subscript Commutativity in C",
        "problem_text": "What is the output of the following program?",
        "code_snippet": "int arr[] = {100, 200, 300};\nprintf(\"%d\", 2[arr]);",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "Compilation Error: invalid subscript"},
            {"id": "B", "text": "200"},
            {"id": "C", "text": "300"},
            {"id": "D", "text": "Garbage value"}
        ],
        "correct_answer": "C",
        "canonical_explanation": "2[arr] expands to *(2 + arr). By commutativity of addition, *(2 + arr) == *(arr + 2) == arr[2]. arr[2] is 300.",
        "difficulty": 0.55,
        "known_misconceptions": ["COMMUTATIVITY_OF_INDEXING_DISBELIEF"]
    },
    # 16. POINTER_ARRAY_RELATION - Hard
    {
        "id": "Q_REL_03",
        "concept_id": "POINTER_ARRAY_RELATION",
        "title": "Modifiable Lvalue Distinction",
        "problem_text": "Which of the following operations will result in a compilation error?",
        "code_snippet": "int arr[5] = {1, 2, 3, 4, 5};\nint *ptr = arr;\n// Line 1: ptr++;\n// Line 2: arr++;",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "Line 1 only"},
            {"id": "B", "text": "Line 2 only"},
            {"id": "C", "text": "Both Line 1 and Line 2"},
            {"id": "D", "text": "Neither Line 1 nor Line 2"}
        ],
        "correct_answer": "B",
        "canonical_explanation": "ptr is a variable pointer and is a modifiable lvalue, so ptr++ is valid. arr is an array name; although it decays to a pointer in expressions, it is NOT a modifiable lvalue. Therefore arr++ fails to compile.",
        "difficulty": 0.7,
        "secondary_concept_ids": ["ARRAY_POINTER_DECAY"],
        "known_misconceptions": ["ARRAY_NAME_IS_POINTER_VARIABLE"]
    },
    # 17. MULTIDIMENSIONAL_ARRAYS - Medium
    {
        "id": "Q_MULTI_01",
        "concept_id": "MULTIDIMENSIONAL_ARRAYS",
        "title": "2D Array Row Major Address Calculation",
        "problem_text": "Given int arr[3][4]; where arr begins at base address 1000 and sizeof(int) = 4. What is the address of arr[2][1]?",
        "code_snippet": "int arr[3][4];",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "1036"},
            {"id": "B", "text": "1032"},
            {"id": "C", "text": "1040"},
            {"id": "D", "text": "1028"}
        ],
        "correct_answer": "A",
        "canonical_explanation": "In row-major order: Address(arr[i][j]) = Base + (i * cols + j) * sizeof(element). Here: 1000 + (2 * 4 + 1) * 4 = 1000 + 9 * 4 = 1036.",
        "difficulty": 0.5,
        "known_misconceptions": ["CONFUSING_ARRAY_OF_POINTERS_WITH_POINTER_TO_ARRAY"]
    },
    # 18. MULTIDIMENSIONAL_ARRAYS - Hard
    {
        "id": "Q_MULTI_02",
        "concept_id": "MULTIDIMENSIONAL_ARRAYS",
        "title": "Pointer to Array vs Pointer Arithmetic on 2D Array",
        "problem_text": "What does the following C code print?",
        "code_snippet": "int a[2][3] = {{1, 2, 3}, {4, 5, 6}};\nint (*p)[3] = a;\np++;\nprintf(\"%d\", **p);",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "2"},
            {"id": "B", "text": "4"},
            {"id": "C", "text": "1"},
            {"id": "D", "text": "Compilation Error"}
        ],
        "correct_answer": "B",
        "canonical_explanation": "p is a pointer to an array of 3 ints. Incrementing p (p++) advances it by sizeof(int[3]) = 3 * sizeof(int) bytes, making it point to the second row {4, 5, 6}. **p dereferences the first element of this second row, giving 4.",
        "difficulty": 0.8,
        "secondary_concept_ids": ["POINTER_ARITHMETIC"],
        "known_misconceptions": ["CONFUSING_ARRAY_OF_POINTERS_WITH_POINTER_TO_ARRAY", "BYTE_INCREMENT_FALLACY"]
    },
    # 19. MULTIDIMENSIONAL_ARRAYS - Hard
    {
        "id": "Q_MULTI_03",
        "concept_id": "MULTIDIMENSIONAL_ARRAYS",
        "title": "Complex Pointer Syntax in 2D Arrays",
        "problem_text": "Given int a[3][3] = {{1,2,3},{4,5,6},{7,8,9}}; what is the value of *(*(a + 1) + 2)?",
        "code_snippet": "int a[3][3] = {{1,2,3},{4,5,6},{7,8,9}};\nint v = *(*(a + 1) + 2);",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "5"},
            {"id": "B", "text": "6"},
            {"id": "C", "text": "7"},
            {"id": "D", "text": "8"}
        ],
        "correct_answer": "B",
        "canonical_explanation": "*(*(a + 1) + 2) is the exact pointer translation of a[1][2]. Row 1 is {4, 5, 6}, and index 2 of that row is 6.",
        "difficulty": 0.7,
        "known_misconceptions": []
    },
    # 20. POINTER_TO_POINTER - Medium
    {
        "id": "Q_P2P_01",
        "concept_id": "POINTER_TO_POINTER",
        "title": "Double Indirection Basics",
        "problem_text": "What is the output of the following program?",
        "code_snippet": "int x = 50;\nint *p = &x;\nint **pp = &p;\n**pp = 100;\nprintf(\"%d %d\", x, *p);",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "50 50"},
            {"id": "B", "text": "100 100"},
            {"id": "C", "text": "50 100"},
            {"id": "D", "text": "100 50"}
        ],
        "correct_answer": "B",
        "canonical_explanation": "pp points to p, and p points to x. Dereferencing twice (**pp) directly modifies x to 100. Since p still points to x, *p also reads 100.",
        "difficulty": 0.45,
        "known_misconceptions": []
    },
    # 21. POINTER_TO_POINTER - Hard
    {
        "id": "Q_P2P_02",
        "concept_id": "POINTER_TO_POINTER",
        "title": "Modifying a Pointer Inside a Function",
        "problem_text": "To allow a function to modify the address held by a pointer in the caller's stack frame (e.g. allocate memory), what parameter type must the function declare?",
        "code_snippet": "void allocate(??? ptr) {\n    *ptr = malloc(100);\n}",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "void*"},
            {"id": "B", "text": "int*"},
            {"id": "C", "text": "int** (or T** for type T)"},
            {"id": "D", "text": "int&"}
        ],
        "correct_answer": "C",
        "canonical_explanation": "In C, all arguments are passed by value. To modify an object in the caller, you must pass a pointer to that object. To modify a pointer (T*), you must pass a pointer to that pointer (T**).",
        "difficulty": 0.7,
        "known_misconceptions": ["DOUBLE_POINTER_EQUALS_2D_ARRAY"]
    },
    # 22. POINTER_TO_POINTER - Hard
    {
        "id": "Q_P2P_03",
        "concept_id": "POINTER_TO_POINTER",
        "title": "Pointer to Pointer Incompatibility with 2D Arrays",
        "problem_text": "Why does passing a 2D array int a[3][3] to a function expecting int **ptr generate a compiler warning and crash at runtime upon dereferencing?",
        "code_snippet": "void print_matrix(int **p);\nint a[3][3];\nprint_matrix(a); // Warning + crash on p[0][0]",
        "question_type": "MCQ",
        "options": [
            {"id": "A", "text": "Because 2D arrays are stored in column-major order in C"},
            {"id": "B", "text": "Because a decays to int (*)[3] (pointer to row array), while int** expects a pointer to pointer table of addresses"},
            {"id": "C", "text": "Because C does not allow pointers to be passed to functions"},
            {"id": "D", "text": "Because sizeof(int) is 4 bytes while sizeof(int*) is 8 bytes on all systems"}
        ],
        "correct_answer": "B",
        "canonical_explanation": "A 2D array in C is a contiguous block of integers. When 'a' decays, its type is int (*)[3]. An int** expects an array of memory addresses that each point to separate row buffers. Treating elements of the first row as memory addresses causes invalid pointer dereferences.",
        "difficulty": 0.85,
        "secondary_concept_ids": ["MULTIDIMENSIONAL_ARRAYS"],
        "known_misconceptions": ["DOUBLE_POINTER_EQUALS_2D_ARRAY"]
    }
]

