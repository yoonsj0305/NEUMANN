Traceback (most recent call last):
  File "/home/user/NEUMANN/stage2/c1.py", line 376, in <module>
    main()
  File "/home/user/NEUMANN/stage2/c1.py", line 372, in main
    {"check": cmd_check, "train": cmd_train, "select": cmd_select, "diag": cmd_diag, "report": cmd_report}[a.cmd](a)
  File "/home/user/NEUMANN/stage2/c1.py", line 294, in cmd_report
    B = baselines(t)
        ^^^^^^^^^^^^
  File "/home/user/NEUMANN/stage2/c1.py", line 277, in baselines
    accs = [fin_of(d)["judgment"]["acc"] for d in BASE_ACC[task]]
            ~~~~~~~~~^^^^^^^^^^^^
KeyError: 'judgment'
