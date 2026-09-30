#pragma once

#include "CoreMinimal.h"
#include "BrawlerTypes.generated.h"

class UPaperSprite;

/**
 * Belt-Scroll-Koordinatensystem
 * -----------------------------
 * Spiellogik arbeitet mit (X, Depth, Height):
 *   X      = horizontal (rechts +)
 *   Depth  = Tiefe im Laufband (0 = vorne/unten am Bildschirm, DepthMax = hinten)
 *   Height = Hoehe ueber dem Boden (Sprung, Wurf)
 *
 * Welt:  X = X,  Y = -Depth (Kamera steht bei +Y und schaut nach -Y),  Z = Depth + Height
 * Damit wandern Figuren weiter hinten auf dem Bildschirm nach oben – wie in Streets of Rage.
 */
namespace Brawler
{
	constexpr float DepthMin = 0.f;
	constexpr float DepthMax = 240.f;
	constexpr float FloorTopZ = 300.f;
	constexpr float Gravity = 2600.f;

	constexpr float ScreenWidth = 1600.f;
	constexpr float ScreenHeight = 900.f;
	constexpr float CameraZ = 340.f;
	constexpr float CameraY = 2000.f;
	constexpr float StageEndX = 8192.f;

	/** Charakter-Frames: 320x320, Fuesse bei y=312 */
	constexpr float CharFrameSize = 320.f;
	constexpr float CharFootY = 312.f;

	/** Koerpermasse fuer Treffer-Tests */
	constexpr float BodyHalfWidth = 26.f;
	constexpr float BodyHeight = 170.f;

	/** Sortier-Prioritaeten fuer transluzente Sprites */
	constexpr int32 SortSky = -3000;
	constexpr int32 SortWall = -2500;
	constexpr int32 SortFloor = -2400;
	constexpr int32 SortShadow = -2000;
	constexpr int32 SortActorBase = 0;      // + (DepthMax - Depth) * 4
	constexpr int32 SortEffects = 2000;
	constexpr int32 SortForeground = 3000;

	inline FVector ToWorld(float X, float Depth, float Height)
	{
		return FVector(X, -Depth, Depth + Height);
	}

	inline int32 SortForDepth(float Depth, int32 Offset = 0)
	{
		return SortActorBase + FMath::RoundToInt((DepthMax + 50.f - Depth) * 4.f) + Offset;
	}
}

UENUM(BlueprintType)
enum class EBrawlerTeam : uint8
{
	Player,
	Enemy,
	Neutral
};

UENUM(BlueprintType)
enum class EFighterState : uint8
{
	Idle,
	Walk,
	Attack,
	Jump,
	Hurt,
	Grabbing,
	Grabbed,
	Falling,
	Down,
	GetUp,
	Pickup,
	Dead,
	Victory
};

UENUM(BlueprintType)
enum class EHitType : uint8
{
	Light,      // kurzer Hitstun
	Heavy,      // laengerer Hitstun, staerkerer Rueckstoss
	Knockdown   // wirft zu Boden
};

UENUM(BlueprintType)
enum class EEnemyStyle : uint8
{
	Punk,
	Skater,
	Heavy,
	Kicker,  // Kickboxerin: schnelle Kicks, fliegender Roundhouse
	Suit     // Anzug-Boss mit Spieler-Moveset (Harald)
};

/** Beschreibung eines Angriffs (Frames, Reichweite, Wirkung). */
struct FBrawlerAttack
{
	FName Anim;
	/** Aktive Frames (Index im Sprite-Flipbook, inklusiv) */
	int32 ActiveStart = 1;
	int32 ActiveEnd = 1;
	float Damage = 5.f;
	/** Horizontaler Trefferbereich relativ zur Blickrichtung */
	float ReachMin = 0.f;
	float ReachMax = 90.f;
	float DepthRange = 26.f;
	/** Vertikaler Trefferbereich relativ zu den eigenen Fuessen */
	float HeightMin = 40.f;
	float HeightMax = 190.f;
	EHitType HitType = EHitType::Light;
	float Knockback = 80.f;
	float Launch = 0.f;
	float Hitstop = 0.07f;
	/** Vorwaertsbewegung waehrend des Angriffs (Units/s) */
	float Lunge = 0.f;
	bool bHitsBehind = false;
	bool bHitsBothSides = false;
	/** Darf dasselbe Ziel mehrfach treffen (je aktivem Frame) */
	bool bMultiHit = false;
	/** Wird die Animation schneller/langsamer abgespielt? 0 = Standard */
	float FPS = 0.f;
	/** Ab welchem Frame darf der naechste Combo-Schlag starten */
	int32 CancelFrame = 2;
	/** Unverwundbar waehrend des Angriffs (Spezialangriff) */
	bool bInvulnerable = false;
	/** Kostet Lebensenergie (Spezialangriff, wie in SoR4 rueckgewinnbar) */
	float HealthCost = 0.f;
	/** Animation loopen und nach Duration Sekunden beenden (z.B. Sturmangriff) */
	bool bLoopAnim = false;
	float Duration = 0.f;
	/** Sound beim Ausholen */
	bool bWhoosh = true;
	/** Waffenschlag (verbraucht Haltbarkeit) */
	FName Weapon;
	/** Sprungangriff (Gegner springen dabei ab) */
	bool bJump = false;
};

/** Frames einer Sprite-Animation */
USTRUCT()
struct FBrawlerAnimFrames
{
	GENERATED_BODY()

	UPROPERTY()
	TArray<TObjectPtr<UPaperSprite>> Frames;
};

/** Gegner-Profil (Werte fuer einen Gegnertyp) */
struct FEnemyProfile
{
	FName Type;
	FString SpriteSet;
	FString DisplayName;
	EEnemyStyle Style = EEnemyStyle::Punk;
	float MaxHealth = 60.f;
	float WalkSpeed = 170.f;
	float Scale = 1.f;
	int32 Score = 100;
	bool bGrabbable = true;
	/** Anzahl leichter Treffer, die ohne Hitstun eingesteckt werden (Super-Armor) */
	int32 Armor = 0;
	float AttackCooldown = 1.4f;
	/** Boss: eigene Lebensleiste, Wut-Phase, Stage endet mit seinem Sieg */
	bool bBoss = false;
	/** Startwaffe (z.B. Knife, Bat, Golf) */
	FName Weapon;
	/** Ruft bei 66 % und 33 % Energie Verstaerkung */
	TArray<FName> Summons;
	float ShadowScale = 1.f;
};
