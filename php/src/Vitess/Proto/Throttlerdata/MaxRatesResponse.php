<?php
// DO NOT EDIT! Generated by Protobuf-PHP protoc plugin 1.0
// Source: throttlerdata.proto

namespace Vitess\Proto\Throttlerdata {

  class MaxRatesResponse extends \DrSlump\Protobuf\Message {

    /**  @var \Vitess\Proto\Throttlerdata\MaxRatesResponse\RatesEntry[]  */
    public $rates = array();
    

    /** @var \Closure[] */
    protected static $__extensions = array();

    public static function descriptor()
    {
      $descriptor = new \DrSlump\Protobuf\Descriptor(__CLASS__, 'throttlerdata.MaxRatesResponse');

      // REPEATED MESSAGE rates = 1
      $f = new \DrSlump\Protobuf\Field();
      $f->number    = 1;
      $f->name      = "rates";
      $f->type      = \DrSlump\Protobuf::TYPE_MESSAGE;
      $f->rule      = \DrSlump\Protobuf::RULE_REPEATED;
      $f->reference = '\Vitess\Proto\Throttlerdata\MaxRatesResponse\RatesEntry';
      $descriptor->addField($f);

      foreach (self::$__extensions as $cb) {
        $descriptor->addField($cb(), true);
      }

      return $descriptor;
    }

    /**
     * Check if <rates> has a value
     *
     * @return boolean
     */
    public function hasRates(){
      return $this->_has(1);
    }
    
    /**
     * Clear <rates> value
     *
     * @return \Vitess\Proto\Throttlerdata\MaxRatesResponse
     */
    public function clearRates(){
      return $this->_clear(1);
    }
    
    /**
     * Get <rates> value
     *
     * @param int $idx
     * @return \Vitess\Proto\Throttlerdata\MaxRatesResponse\RatesEntry
     */
    public function getRates($idx = NULL){
      return $this->_get(1, $idx);
    }
    
    /**
     * Set <rates> value
     *
     * @param \Vitess\Proto\Throttlerdata\MaxRatesResponse\RatesEntry $value
     * @return \Vitess\Proto\Throttlerdata\MaxRatesResponse
     */
    public function setRates(\Vitess\Proto\Throttlerdata\MaxRatesResponse\RatesEntry $value, $idx = NULL){
      return $this->_set(1, $value, $idx);
    }
    
    /**
     * Get all elements of <rates>
     *
     * @return \Vitess\Proto\Throttlerdata\MaxRatesResponse\RatesEntry[]
     */
    public function getRatesList(){
     return $this->_get(1);
    }
    
    /**
     * Add a new element to <rates>
     *
     * @param \Vitess\Proto\Throttlerdata\MaxRatesResponse\RatesEntry $value
     * @return \Vitess\Proto\Throttlerdata\MaxRatesResponse
     */
    public function addRates(\Vitess\Proto\Throttlerdata\MaxRatesResponse\RatesEntry $value){
     return $this->_add(1, $value);
    }
  }
}

