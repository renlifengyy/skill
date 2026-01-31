; Align selected segPath segments to a fixed pitch.
; Usage:
;   skillAlignSegPathPrompt()
; or
;   skillAlignSegPathToPitch(0.2)

procedure(_skillAlignCoord(coord pitch)
  round(coord / pitch) * pitch
)

procedure(skillAlignSegPathCheck()
  let((missing)
    missing = nil
    unless(getd('geGetSelSet)
      missing = cons("geGetSelSet" missing)
    )
    unless(getd('hiGetFloat)
      missing = cons("hiGetFloat" missing)
    )
    unless(getd('round)
      missing = cons("round" missing)
    )
    when(missing
      error(sprintf(nil "Missing required SKILL APIs: %L" reverse(missing)))
    )
    t
  )
)

procedure(skillAlignSegPathToPitch(pitch)
  let((sel)
    skillAlignSegPathCheck()
    when(pitch <= 0
      error("Pitch must be > 0")
    )
    sel = geGetSelSet()
    foreach(obj sel
      when(obj~>objType == "segPath"
        let((points count i prev curr xAligned yAligned)
          points = copy(obj~>points)
          count = length(points)
          for(i 1 (count - 1)
            prev = nth(i - 1 points)
            curr = nth(i points)
            when(prev && curr
              if(car(prev) == car(curr) then
                xAligned = _skillAlignCoord(car(curr) pitch)
                setcar(prev xAligned)
                setcar(curr xAligned)
              else
                when(cadr(prev) == cadr(curr)
                  yAligned = _skillAlignCoord(cadr(curr) pitch)
                  setcar(cdr(prev) yAligned)
                  setcar(cdr(curr) yAligned)
                )
              )
            )
          )
          obj~>points = points
        )
      )
    )
  )
)

procedure(skillAlignSegPathPrompt()
  let((pitch)
    pitch = hiGetFloat("Align segPath spacing (pitch):")
    when(pitch
      skillAlignSegPathToPitch(pitch)
    )
  )
)
