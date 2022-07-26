# Tabula Messages

## Parameter Tree

The parameter tree dictates:
- how a particular parameter type (i.e., Text Content) can be changed
- how changing a particular parameter type will affect other parameters down the tree

```
-- World (*)
    |
    |-- Program
        |
        |-- Recording (d)
            |
            |-- Text Content (*db)
            |   |
            |   |-- Label Interval (*d)
            |       |
            |       |-- Label (*d)
            |
            |-- User Sequence (+db)
                |
                |-- Plan (d)
                    |
                    |-- Waypoint (pd)
                        |
                        |-- Task Subsequence (qd)
                            |
                            |-- Command (rd)
                            |
                            |-- Conditional (rd)
                            |
                            |-- Jump Point (rd)


KEY:
(*)  --  Parameter is directly editable.
(+)  --  Paths between waypoints are directly editable.
(d)  --  Deletable.
(b)  --  Redoable (equivalent to deleting and re-recording).
(q)  --  Rearrangeable. 
(p)  --  Confirm (lock), deny (prevent) from adding to user seq., or unrestricted.
(r)  --  Confirm (lock), deny (prevent) from adding to task seq., or unrestricted.
```


## Message Structure

The structure of the json string within ```TabulaUpdate.msg```:

```
{
  "world":
  {
    "regions":
    {
      REGION_NAME: 
      {
        "name": REGION_NAME (string),
        "objects":
        [
          "name": OBJECT_NAME (string)
          "objects": [ ... ]
        ]
      }
    }
  }

  "program":
  {
    "recordings":
    {
      RECORDING_ID (int):
      {
        "text":
        {
          "data": CONTENT (string),
          "label_intervals": 
          [
            {
              "start": START_POS (int),
              "end": END_POS (int),
              "label": LABEL (string)
            }
            ...
          ]
        }
        "sketch":
        {
          "user_sequence":
          {
            "data":
            [
              {
                "cmd": ACTION_NAME (string),
                "type": CATEGORICAL ("command", "conditional")
                "args":
                {
                  ARG_NAME (string): ARG_VAL (string),
                  ...
                }
              }
              ...
            ]
            "plan":
            {
              "waypoints":
              {
                WAYPOINT_ID (int):
                {
                  "x": X_POS (int),
                  "y": Y_POS (int),
                  "task_subsequence":
                  [
                    {
                      "cmd": ACTION_NAME (string),
                      "type": CATEGORICAL ("command", "conditional")
                      "args":
                      {
                        ARG_NAME (string): ARG_VAL (string),
                        ...
                      }
                    }
                  ]
                }
                ...
              }
            }
          }
        }
      }
      ...
    }
  }
}
```