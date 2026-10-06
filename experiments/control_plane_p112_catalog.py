"""P1.12 fresh opened-development catalog, frozen before any P1.12 model score."""
from copy import deepcopy
from neumann1.control_plane_p112_semantic import SEMANTIC_INSTRUCTIONS

ROWS = [
    {
        "task_id": "p112d_b01",
        "stratum": "B_MULTI_FEASIBLE_JOINT_CROSS_ENCODER",
        "view": {
            "instruction": "X is the certificate revocation list and Y is the trusted timestamp authority. Resolve 'It' to the service that certifies when a digital record existed, then return a complete assignment.",
            "public": {
                "query": "Choose X, Y from {101,103}. X differs from Y, It equals 103. Return a complete assignment."
            }
        }
    },
    {
        "task_id": "p112d_b02",
        "stratum": "B_MULTI_FEASIBLE_JOINT_CROSS_ENCODER",
        "view": {
            "instruction": "A is the associative map, B is the stack, and C is the heap. Resolve 'It' to the container retrieving stored records by lookup key, then return a complete assignment.",
            "public": {
                "query": "Choose A, B, C from {13,27,41}. A differs from B, A differs from C, B differs from C, It equals 41. Return a complete assignment."
            }
        }
    },
    {
        "task_id": "p112d_b03",
        "stratum": "B_MULTI_FEASIBLE_JOINT_CROSS_ENCODER",
        "view": {
            "instruction": "P is the planetary coronagraph, Q is the spectrometer, R is the radio dish, and S is the photometer. Resolve 'It' to the instrument that spreads incoming electromagnetic radiation into different wavelengths, then return a complete assignment.",
            "public": {
                "query": "Choose P, Q, R, S from {3,17,31,53}. P differs from Q, P differs from R, P differs from S, Q differs from R, Q differs from S, R differs from S, It equals 31. Return a complete assignment."
            }
        }
    },
    {
        "task_id": "p112d_b04",
        "stratum": "B_MULTI_FEASIBLE_JOINT_CROSS_ENCODER",
        "view": {
            "instruction": "M is the lysosome and N is the ribosome. Resolve 'It' to the cellular machinery translating messenger RNA into chains of amino acids, then return a complete assignment.",
            "public": {
                "query": "Choose M, N from {-33,-22}. M differs from N, It equals -22. Return a complete assignment."
            }
        }
    },
    {
        "task_id": "p112d_b05",
        "stratum": "B_MULTI_FEASIBLE_JOINT_CROSS_ENCODER",
        "view": {
            "instruction": "A is the transfer warehouse, B is the cold-storage facility, and C is the cross-dock terminal. Resolve 'It' to the hub moving incoming freight straight onto outgoing vehicles without long dwell time, then return a complete assignment.",
            "public": {
                "query": "Choose A, B, C from {12,24,48}. A differs from B, A differs from C, B differs from C, It equals 24. Return a complete assignment."
            }
        }
    },
    {
        "task_id": "p112d_b06",
        "stratum": "B_MULTI_FEASIBLE_JOINT_CROSS_ENCODER",
        "view": {
            "instruction": "P is the demodulator, Q is the equalizer, R is the interleaver, and S is the frequency synthesizer. Resolve 'It' to the circuit recovering the original message bits from a modulated waveform, then return a complete assignment.",
            "public": {
                "query": "Choose P, Q, R, S from {19,23,29,37}. P differs from Q, P differs from R, P differs from S, Q differs from R, Q differs from S, R differs from S, It equals 19. Return a complete assignment."
            }
        }
    },
    {
        "task_id": "p112d_b07",
        "stratum": "B_MULTI_FEASIBLE_JOINT_CROSS_ENCODER",
        "view": {
            "instruction": "M is the request dispatcher, N is the consensus engine, and O is the cache eviction policy. Resolve 'It' to the protocol component bringing replicas to agreement on operation ordering, then return a complete assignment.",
            "public": {
                "query": "Choose M, N, O from {115,215,315}. M differs from N, M differs from O, N differs from O, It equals 215. Return a complete assignment."
            }
        }
    },
    {
        "task_id": "p112d_b08",
        "stratum": "B_MULTI_FEASIBLE_JOINT_CROSS_ENCODER",
        "view": {
            "instruction": "X is the annealing furnace and Y is the milling cutter. Resolve 'It' to the equipment that softens work-hardened metal through controlled heating, then return a complete assignment.",
            "public": {
                "query": "Choose X, Y from {700,900}. X differs from Y, It equals 700. Return a complete assignment."
            }
        }
    },
    {
        "task_id": "p112d_b09",
        "stratum": "B_MULTI_FEASIBLE_JOINT_CROSS_ENCODER",
        "view": {
            "instruction": "A is the rudder, B is the propeller, and C is the ballast tank. Resolve 'It' to the vessel compartment admitting seawater to adjust buoyancy, then return a complete assignment.",
            "public": {
                "query": "Choose A, B, C from {-21,-7,14}. A differs from B, A differs from C, B differs from C, It equals 14. Return a complete assignment."
            }
        }
    },
    {
        "task_id": "p112d_b10",
        "stratum": "B_MULTI_FEASIBLE_JOINT_CROSS_ENCODER",
        "view": {
            "instruction": "P is the optical fiber coupler, Q is the polarization rotator, R is the diffraction grating, and S is the photomultiplier. Resolve 'It' to the periodic surface splitting white illumination into colored beams through interference, then return a complete assignment.",
            "public": {
                "query": "Choose P, Q, R, S from {42,56,70,84}. P differs from Q, P differs from R, P differs from S, Q differs from R, Q differs from S, R differs from S, It equals 70. Return a complete assignment."
            }
        }
    },
    {
        "task_id": "p112d_b11",
        "stratum": "B_MULTI_FEASIBLE_JOINT_CROSS_ENCODER",
        "view": {
            "instruction": "M is the amygdala, N is the hippocampus, and O is the cerebellum. Resolve 'It' to the brain region supporting long-term formation of autobiographical recollections, then return a complete assignment.",
            "public": {
                "query": "Choose M, N, O from {16,32,96}. M differs from N, M differs from O, N differs from O, It equals 32. Return a complete assignment."
            }
        }
    },
    {
        "task_id": "p112d_b12",
        "stratum": "B_MULTI_FEASIBLE_JOINT_CROSS_ENCODER",
        "view": {
            "instruction": "X is the checksum calculator and Y is the watchdog timer. Resolve 'It' to the hardware supervisor that resets unresponsive embedded software, then return a complete assignment.",
            "public": {
                "query": "Choose X, Y from {510,1020}. X differs from Y, It equals 1020. Return a complete assignment."
            }
        }
    }
]
REFS = [
    {
        "task_id": "p112d_b01",
        "family": "constraint_planning",
        "expected_candidate": 1,
        "semantic_grounding": "A trusted timestamp authority attests the existence of a record at a time.",
        "private": {
            "domains": {
                "X": [
                    101,
                    103
                ],
                "Y": [
                    101,
                    103
                ]
            },
            "constraints": [
                [
                    "ne",
                    "X",
                    "Y"
                ],
                [
                    "eq",
                    "Y",
                    103
                ]
            ]
        },
        "witness": {
            "Y": 103,
            "X": 101
        }
    },
    {
        "task_id": "p112d_b02",
        "family": "constraint_planning",
        "expected_candidate": 0,
        "semantic_grounding": "An associative map retrieves stored values using keys.",
        "private": {
            "domains": {
                "A": [
                    13,
                    27,
                    41
                ],
                "B": [
                    13,
                    27,
                    41
                ],
                "C": [
                    13,
                    27,
                    41
                ]
            },
            "constraints": [
                [
                    "ne",
                    "A",
                    "B"
                ],
                [
                    "ne",
                    "A",
                    "C"
                ],
                [
                    "ne",
                    "B",
                    "C"
                ],
                [
                    "eq",
                    "A",
                    41
                ]
            ]
        },
        "witness": {
            "A": 41,
            "B": 13,
            "C": 27
        }
    },
    {
        "task_id": "p112d_b03",
        "family": "constraint_planning",
        "expected_candidate": 1,
        "semantic_grounding": "A spectrometer separates an incoming signal into its spectral wavelengths.",
        "private": {
            "domains": {
                "P": [
                    3,
                    17,
                    31,
                    53
                ],
                "Q": [
                    3,
                    17,
                    31,
                    53
                ],
                "R": [
                    3,
                    17,
                    31,
                    53
                ],
                "S": [
                    3,
                    17,
                    31,
                    53
                ]
            },
            "constraints": [
                [
                    "ne",
                    "P",
                    "Q"
                ],
                [
                    "ne",
                    "P",
                    "R"
                ],
                [
                    "ne",
                    "P",
                    "S"
                ],
                [
                    "ne",
                    "Q",
                    "R"
                ],
                [
                    "ne",
                    "Q",
                    "S"
                ],
                [
                    "ne",
                    "R",
                    "S"
                ],
                [
                    "eq",
                    "Q",
                    31
                ]
            ]
        },
        "witness": {
            "Q": 31,
            "P": 3,
            "R": 17,
            "S": 53
        }
    },
    {
        "task_id": "p112d_b04",
        "family": "constraint_planning",
        "expected_candidate": 1,
        "semantic_grounding": "A ribosome reads messenger RNA to synthesize a polypeptide.",
        "private": {
            "domains": {
                "M": [
                    -33,
                    -22
                ],
                "N": [
                    -33,
                    -22
                ]
            },
            "constraints": [
                [
                    "ne",
                    "M",
                    "N"
                ],
                [
                    "eq",
                    "N",
                    -22
                ]
            ]
        },
        "witness": {
            "N": -22,
            "M": -33
        }
    },
    {
        "task_id": "p112d_b05",
        "family": "constraint_planning",
        "expected_candidate": 2,
        "semantic_grounding": "A cross-dock terminal transfers arriving freight to departing vehicles with minimal storage.",
        "private": {
            "domains": {
                "A": [
                    12,
                    24,
                    48
                ],
                "B": [
                    12,
                    24,
                    48
                ],
                "C": [
                    12,
                    24,
                    48
                ]
            },
            "constraints": [
                [
                    "ne",
                    "A",
                    "B"
                ],
                [
                    "ne",
                    "A",
                    "C"
                ],
                [
                    "ne",
                    "B",
                    "C"
                ],
                [
                    "eq",
                    "C",
                    24
                ]
            ]
        },
        "witness": {
            "C": 24,
            "A": 12,
            "B": 48
        }
    },
    {
        "task_id": "p112d_b06",
        "family": "constraint_planning",
        "expected_candidate": 0,
        "semantic_grounding": "A demodulator recovers encoded information from a modulated carrier.",
        "private": {
            "domains": {
                "P": [
                    19,
                    23,
                    29,
                    37
                ],
                "Q": [
                    19,
                    23,
                    29,
                    37
                ],
                "R": [
                    19,
                    23,
                    29,
                    37
                ],
                "S": [
                    19,
                    23,
                    29,
                    37
                ]
            },
            "constraints": [
                [
                    "ne",
                    "P",
                    "Q"
                ],
                [
                    "ne",
                    "P",
                    "R"
                ],
                [
                    "ne",
                    "P",
                    "S"
                ],
                [
                    "ne",
                    "Q",
                    "R"
                ],
                [
                    "ne",
                    "Q",
                    "S"
                ],
                [
                    "ne",
                    "R",
                    "S"
                ],
                [
                    "eq",
                    "P",
                    19
                ]
            ]
        },
        "witness": {
            "P": 19,
            "Q": 23,
            "R": 29,
            "S": 37
        }
    },
    {
        "task_id": "p112d_b07",
        "family": "constraint_planning",
        "expected_candidate": 1,
        "semantic_grounding": "A consensus engine coordinates distributed replicas to agree on ordered operations.",
        "private": {
            "domains": {
                "M": [
                    115,
                    215,
                    315
                ],
                "N": [
                    115,
                    215,
                    315
                ],
                "O": [
                    115,
                    215,
                    315
                ]
            },
            "constraints": [
                [
                    "ne",
                    "M",
                    "N"
                ],
                [
                    "ne",
                    "M",
                    "O"
                ],
                [
                    "ne",
                    "N",
                    "O"
                ],
                [
                    "eq",
                    "N",
                    215
                ]
            ]
        },
        "witness": {
            "N": 215,
            "M": 115,
            "O": 315
        }
    },
    {
        "task_id": "p112d_b08",
        "family": "constraint_planning",
        "expected_candidate": 0,
        "semantic_grounding": "An annealing furnace performs a thermal treatment to restore ductility.",
        "private": {
            "domains": {
                "X": [
                    700,
                    900
                ],
                "Y": [
                    700,
                    900
                ]
            },
            "constraints": [
                [
                    "ne",
                    "X",
                    "Y"
                ],
                [
                    "eq",
                    "X",
                    700
                ]
            ]
        },
        "witness": {
            "X": 700,
            "Y": 900
        }
    },
    {
        "task_id": "p112d_b09",
        "family": "constraint_planning",
        "expected_candidate": 2,
        "semantic_grounding": "A ballast tank holds or expels water to change a vessel's buoyancy.",
        "private": {
            "domains": {
                "A": [
                    -21,
                    -7,
                    14
                ],
                "B": [
                    -21,
                    -7,
                    14
                ],
                "C": [
                    -21,
                    -7,
                    14
                ]
            },
            "constraints": [
                [
                    "ne",
                    "A",
                    "B"
                ],
                [
                    "ne",
                    "A",
                    "C"
                ],
                [
                    "ne",
                    "B",
                    "C"
                ],
                [
                    "eq",
                    "C",
                    14
                ]
            ]
        },
        "witness": {
            "C": 14,
            "A": -21,
            "B": -7
        }
    },
    {
        "task_id": "p112d_b10",
        "family": "constraint_planning",
        "expected_candidate": 2,
        "semantic_grounding": "A diffraction grating separates wavelengths through interference.",
        "private": {
            "domains": {
                "P": [
                    42,
                    56,
                    70,
                    84
                ],
                "Q": [
                    42,
                    56,
                    70,
                    84
                ],
                "R": [
                    42,
                    56,
                    70,
                    84
                ],
                "S": [
                    42,
                    56,
                    70,
                    84
                ]
            },
            "constraints": [
                [
                    "ne",
                    "P",
                    "Q"
                ],
                [
                    "ne",
                    "P",
                    "R"
                ],
                [
                    "ne",
                    "P",
                    "S"
                ],
                [
                    "ne",
                    "Q",
                    "R"
                ],
                [
                    "ne",
                    "Q",
                    "S"
                ],
                [
                    "ne",
                    "R",
                    "S"
                ],
                [
                    "eq",
                    "R",
                    70
                ]
            ]
        },
        "witness": {
            "R": 70,
            "P": 42,
            "Q": 56,
            "S": 84
        }
    },
    {
        "task_id": "p112d_b11",
        "family": "constraint_planning",
        "expected_candidate": 1,
        "semantic_grounding": "The hippocampus is important for forming new episodic memories.",
        "private": {
            "domains": {
                "M": [
                    16,
                    32,
                    96
                ],
                "N": [
                    16,
                    32,
                    96
                ],
                "O": [
                    16,
                    32,
                    96
                ]
            },
            "constraints": [
                [
                    "ne",
                    "M",
                    "N"
                ],
                [
                    "ne",
                    "M",
                    "O"
                ],
                [
                    "ne",
                    "N",
                    "O"
                ],
                [
                    "eq",
                    "N",
                    32
                ]
            ]
        },
        "witness": {
            "N": 32,
            "M": 16,
            "O": 96
        }
    },
    {
        "task_id": "p112d_b12",
        "family": "constraint_planning",
        "expected_candidate": 1,
        "semantic_grounding": "A watchdog timer detects a lack of progress and can trigger a reset.",
        "private": {
            "domains": {
                "X": [
                    510,
                    1020
                ],
                "Y": [
                    510,
                    1020
                ]
            },
            "constraints": [
                [
                    "ne",
                    "X",
                    "Y"
                ],
                [
                    "eq",
                    "Y",
                    1020
                ]
            ]
        },
        "witness": {
            "Y": 1020,
            "X": 510
        }
    }
]

def catalog():
    rows,refs=deepcopy(ROWS),deepcopy(REFS)
    if [r["view"]["instruction"] for r in rows] != list(SEMANTIC_INSTRUCTIONS):
        raise ValueError("P1.12 catalog semantic registry drift")
    return rows,refs

def negative_controls():
    rows,_=catalog()
    return (
      {"instruction":"Unregistered P1.12 instruction.","public":rows[0]["view"]["public"]},
      {"instruction":rows[0]["view"]["instruction"],"public":{"query":"Choose X, Y from {101,103}. It equals 103, It equals 101. Return a complete assignment."}},
      {"instruction":rows[1]["view"]["instruction"],"public":{"query":"Choose A, B, C, D, E from {1,2,3,4,5}. It equals 3. Return a complete assignment."}},
      {"instruction":rows[2]["view"]["instruction"],"public":{"query":"Choose P, Q, R from {3,17,31}. P mirrors Q, It equals 31. Return a complete assignment."}},
    )
