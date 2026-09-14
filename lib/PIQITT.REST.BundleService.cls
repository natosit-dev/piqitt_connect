Class PIQITT.REST.BundleService Extends %CSP.REST
{

Parameter HandleCorsRequest = 1;

XData UrlMap
{
<Routes>
  <Route Url="/bundle" Method="POST" Call="PostBundle"/>
  <Route Url="/bundle/:id" Method="GET" Call="GetBundle"/>
  <Route Url="/bundles" Method="GET" Call="ListBundles"/>
  <Route Url="/wipe" Method="POST" Call="Wipe"/>
</Routes>
}

ClassMethod CorsHeaders()
{
  Do %response.SetHeader("Access-Control-Allow-Origin","*")
  Do %response.SetHeader("Access-Control-Allow-Headers","Content-Type, Authorization, Accept")
  Do %response.SetHeader("Access-Control-Allow-Methods","GET, POST, OPTIONS")
}

ClassMethod OnPreDispatch(pUrl As %String, pMethod As %String, ByRef pContinue As %Boolean) As %Status
{
  Do ..CorsHeaders()
  Set pContinue = 1
  Return $$$OK
}

ClassMethod WriteJson(status As %Integer, obj As %DynamicAbstractObject) As %Status
{
  Set %response.Status = status
  Do %response.SetHeader("Content-Type","application/json")
  Write obj.%ToJSON()
  Return $$$OK
}

ClassMethod CodeableConceptLabel(cc As %DynamicObject) As %String
{
  If '$IsObject(cc) Quit ""
  Set t = cc.%Get("text")
  If t'="" Quit t
  Set coding = cc.%Get("coding")
  If $IsObject(coding), (coding.%Size()>0) {
    Set c0 = coding.%Get(0)
    If $IsObject(c0) {
      Set d = c0.%Get("display")
      If d'="" Quit d
      Set c = c0.%Get("code")
      Quit $Get(c)
    }
  }
  Quit ""
}

ClassMethod CodeableConceptFirstCode(cc As %DynamicObject) As %String
{
  If '$IsObject(cc) Quit ""
  Set coding = cc.%Get("coding")
  If $IsObject(coding), (coding.%Size()>0) {
    Set c0 = coding.%Get(0)
    If $IsObject(c0) {
      Set c = c0.%Get("code")
      Quit $Get(c)
    }
  }
  Quit ""
}

ClassMethod IsPIQIObservation(codeObj As %DynamicObject) As %Boolean
{
  If '$IsObject(codeObj) Quit 0
  Set label = ..CodeableConceptLabel(codeObj)
  If ($ZCONVERT(label,"L")["piqi") Quit 1
  Set firstCode = ..CodeableConceptFirstCode(codeObj)
  If $Extract(firstCode,1,5)="PIQI-" Quit 1
  Quit 0
}

ClassMethod GetValueQuantityValue(vq As %DynamicObject) As %String
{
  If '$IsObject(vq) Quit ""
  Set v = vq.%Get("value")
  Quit $Get(v)
}

ClassMethod PostBundle() As %Status
{
  Try {
    Set raw = %request.Content.Read()
    If raw = "" {
      Set err = ##class(%DynamicObject).%New()
      Do err.%Set("error","Empty request body")
      Do ..WriteJson(400, err)
      Return $$$OK
    }

    Set obj = ##class(%DynamicObject).%FromJSON(raw)

    If obj.%Get("resourceType")'="Bundle" {
      Set err = ##class(%DynamicObject).%New()
      Do err.%Set("error","Expected resourceType=Bundle")
      Do ..WriteJson(400, err)
      Return $$$OK
    }

    Set piqiIndex = ""
    Set piqiWeighted = ""
    Set criticalFails = ""
    Set numer = ""
    Set denom = ""

    Set entries = obj.%Get("entry")
    If $IsObject(entries) {
      For i=0:1:entries.%Size()-1 {
        Set e = entries.%Get(i)
        If '$IsObject(e) Continue
        Set r = e.%Get("resource")
        If '$IsObject(r) Continue
        If r.%Get("resourceType")'="Observation" Continue

        Set codeObj = r.%Get("code")
        If '$IsObject(codeObj) Continue
        If '..IsPIQIObservation(codeObj) Continue

        // PIQI scores are stored and returned on the same 0-100 percentage scale
        // used by PIQIEvaluator and the FHIR Observation valueQuantity.
        Set vqMain = r.%Get("valueQuantity")
        If $IsObject(vqMain) {
          Set pct = ..GetValueQuantityValue(vqMain)
          If pct'="" Set piqiIndex = pct
        }

        Set comps = r.%Get("component")
        If $IsObject(comps) {
          For j=0:1:comps.%Size()-1 {
            Set c = comps.%Get(j)
            If '$IsObject(c) Continue
            Set ccodeObj = c.%Get("code")
            If '$IsObject(ccodeObj) Continue
            Set ccode = ..CodeableConceptFirstCode(ccodeObj)
            Set ccodeU = $ZCONVERT(ccode,"U")

            If ccodeU="PIQI-NUM" {
              Set numer = c.%Get("valueInteger")
              Continue
            }
            If ccodeU="PIQI-DEN" {
              Set denom = c.%Get("valueInteger")
              Continue
            }
            If ccodeU="PIQI-CRIT-FAIL" {
              Set criticalFails = c.%Get("valueInteger")
              Continue
            }
            If ccodeU="PIQI-WINDEX" {
              Set vqW = c.%Get("valueQuantity")
              If $IsObject(vqW) {
                Set pctW = ..GetValueQuantityValue(vqW)
                If pctW'="" Set piqiWeighted = pctW
              }
              Continue
            }
          }
        }

        If (piqiWeighted="") && (piqiIndex'="") Set piqiWeighted = piqiIndex
        Quit
      }
    }

    Set id = $Piece($HOROLOG,",",1)_"-"_$Piece($HOROLOG,",",2)_"-"_$RANDOM(1000000000)
    Set ts = $ZDATETIME($H,3,1)

    Set ^PIQITT("bundle", id) = raw
    Set ^PIQITT("idx", id) = ts_"|"_$Get(piqiIndex)_"|"_$Get(piqiWeighted)_"|"_$Get(criticalFails)_"|"_$Get(numer)_"|"_$Get(denom)

    Set resp = ##class(%DynamicObject).%New()
    Do resp.%Set("id", id)
    Do resp.%Set("storedAt", ts)
    Do resp.%Set("piqiIndex", $Get(piqiIndex))
    Do resp.%Set("piqiWeightedIndex", $Get(piqiWeighted))
    Do resp.%Set("criticalFailureCount", $Get(criticalFails))
    Do resp.%Set("numerator", $Get(numer))
    Do resp.%Set("denominator", $Get(denom))

    Do ..WriteJson(200, resp)
    Return $$$OK

  } Catch ex {
    Set err = ##class(%DynamicObject).%New()
    Do err.%Set("error", ex.DisplayString())
    Do ..WriteJson(500, err)
    Return $$$OK
  }
}

ClassMethod GetBundle(id As %String) As %Status
{
  Set raw = $Get(^PIQITT("bundle", id))
  If raw = "" {
    Set err = ##class(%DynamicObject).%New()
    Do err.%Set("error","Not found")
    Do err.%Set("id", id)
    Do ..WriteJson(404, err)
    Return $$$OK
  }
  Do %response.SetHeader("Content-Type","application/json")
  Write raw
  Return $$$OK
}

ClassMethod ListBundles() As %Status
{
  Set items = ##class(%DynamicArray).%New()
  Set id = ""

  For  Set id=$Order(^PIQITT("idx", id)) Quit:id=""  Do
  . Set rec = ^PIQITT("idx", id)
  . Set ts = $Piece(rec,"|",1)
  . Set piqiIndex = $Piece(rec,"|",2)
  . Set piqiWeighted = $Piece(rec,"|",3)
  . Set criticalFails = $Piece(rec,"|",4)
  . Set numer = $Piece(rec,"|",5)
  . Set denom = $Piece(rec,"|",6)
  . Set row = ##class(%DynamicObject).%New()
  . Do row.%Set("id", id)
  . Do row.%Set("storedAt", ts)
  . Do row.%Set("piqiIndex", $Select(piqiIndex="":"", 1:+piqiIndex))
  . Do row.%Set("piqiWeightedIndex", $Select(piqiWeighted="":"", 1:+piqiWeighted))
  . Do row.%Set("criticalFailureCount", $Select(criticalFails="":"", 1:+criticalFails))
  . Do row.%Set("numerator", $Select(numer="":"", 1:+numer))
  . Do row.%Set("denominator", $Select(denom="":"", 1:+denom))
  . Do items.%Push(row)

  Set resp = ##class(%DynamicObject).%New()
  Do resp.%Set("count", items.%Size())
  Do resp.%Set("items", items)
  Do ..WriteJson(200, resp)
  Return $$$OK
}

ClassMethod Wipe() As %Status
{
  Try {
    Set count = 0
    Set id = ""
    For  Set id=$Order(^PIQITT("idx", id)) Quit:id=""  Set count = count + 1
    Kill ^PIQITT

    Set resp = ##class(%DynamicObject).%New()
    Do resp.%Set("ok", 1)
    Do resp.%Set("deleted", count)
    Do resp.%Set("message", "Cleared ^PIQITT demo data")
    Do ..WriteJson(200, resp)
    Return $$$OK

  } Catch ex {
    Set err = ##class(%DynamicObject).%New()
    Do err.%Set("error", ex.DisplayString())
    Do ..WriteJson(500, err)
    Return $$$OK
  }
}

}
